"""
run_ragas_eval.py
Jalankan semua pertanyaan di data/eval/eval_dataset.json lewat pipeline,
kumpulkan jawaban + context yang dihasilkan sistem, lalu hitung metrik
RAGAS untuk menilai kualitas RAG secara kuantitatif.

Cara kerja:
1. Baca dataset eval (question + ground_truth yang sudah diisi manual)
2. Untuk tiap pertanyaan, jalankan pipeline.ask() -> dapat answer + contexts
   (hasil disimpan sebagai cache, supaya kalau proses RAGAS gagal di tengah,
   tidak perlu ulang panggil pipeline.ask() lagi dari 0 -- ini juga makan kuota)
3. Hitung metrik RAGAS SATU PER SATU per pertanyaan (bukan sekaligus semua),
   dengan progress disimpan tiap kali 1 pertanyaan selesai -- supaya kalau
   kena rate limit di tengah jalan, tinggal jalankan ulang script ini,
   otomatis lanjut dari yang belum selesai, tidak mengulang dari awal.
4. Setelah semua selesai, hitung rata-rata tiap metrik secara manual.
5. Simpan hasil ke data/eval/eval_results.json
"""

import time
import json
import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from src.pipeline import ask

load_dotenv()

EVAL_DATASET_PATH = "data/eval/eval_dataset.json"
EVAL_RESULTS_PATH = "data/eval/eval_results.json"
ENRICHED_CACHE_PATH = "data/eval/enriched_cache.json"
RAGAS_PROGRESS_PATH = "data/eval/ragas_progress.json"

# Set None untuk proses semua pertanyaan. Isi angka (misal 8) untuk
# testing/menghemat kuota dengan subset kecil dulu.
LIMIT_QUESTIONS = None

# Jeda antar pertanyaan saat proses RAGAS satu-per-satu (detik)
DELAY_BETWEEN_QUESTIONS = 8


def load_eval_dataset() -> list:
    """Baca pertanyaan + ground_truth yang sudah diisi manual."""
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if LIMIT_QUESTIONS:
        data = data[:LIMIT_QUESTIONS]
    return data


def run_pipeline_on_dataset(eval_items: list) -> list:
    """
    Jalankan tiap pertanyaan lewat pipeline.ask(). Pertanyaan yang SUDAH
    ada di cache (dari run sebelumnya) di-skip, hanya yang BARU yang
    diproses -- supaya bisa nambah LIMIT_QUESTIONS tanpa mengulang yang
    sudah selesai.
    """
    enriched_items = []

    # Load cache yang sudah ada (kalau ada)
    if os.path.exists(ENRICHED_CACHE_PATH):
        with open(ENRICHED_CACHE_PATH, "r", encoding="utf-8") as f:
            enriched_items = json.load(f)
        print(f"Menemukan {len(enriched_items)} hasil di cache.")

    already_done_questions = {item["question"] for item in enriched_items}

    for item in eval_items:
        if item["question"] in already_done_questions:
            continue  # sudah ada di cache, skip

        print(f"Memproses: {item['question']}")

        max_retries = 3
        result = None
        for attempt in range(max_retries):
            try:
                result = ask(item["question"])
                break
            except Exception as e:
                if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = 15
                    print(f"  Rate limit kena, tunggu {wait_time} detik...")
                    time.sleep(wait_time)
                else:
                    raise

        enriched_items.append({
            "question": item["question"],
            "ground_truth": item["ground_truth"],
            "answer": result["answer"],
            "contexts": [c["text"] for c in result.get("sources_full", [])] or [""],
        })

        # Simpan cache SETIAP KALI 1 pertanyaan baru selesai (bukan nunggu semua selesai)
        os.makedirs(os.path.dirname(ENRICHED_CACHE_PATH), exist_ok=True)
        with open(ENRICHED_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(enriched_items, f, ensure_ascii=False, indent=2)

        time.sleep(2)

    return enriched_items


def get_ragas_llm_and_embeddings():
    """
    RAGAS secara default pakai OpenAI sebagai LLM judge. Di sini kita
    ganti supaya pakai Groq (via langchain-groq), karena kita tidak
    pakai OpenAI.
    """
    groq_llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
         max_tokens=4096,
    )
    ragas_llm = LangchainLLMWrapper(groq_llm)

    hf_embeddings = HuggingFaceEmbeddings(
        model_name="paraphrase-multilingual-MiniLM-L12-v2"
    )
    ragas_embeddings = LangchainEmbeddingsWrapper(hf_embeddings)

    return ragas_llm, ragas_embeddings


def run_ragas_one_by_one(enriched_items: list) -> list:
    """
    Hitung metrik RAGAS SATU PER SATU per pertanyaan, bukan sekaligus.
    Ini lebih lambat, tapi jauh lebih tahan rate limit -- kalau 1
    pertanyaan gagal di tengah, yang lain tetap tersimpan progresnya,
    tidak perlu diulang dari 0 saat script dijalankan lagi.
    """
    ragas_llm, ragas_embeddings = get_ragas_llm_and_embeddings()

    all_results = []
    if os.path.exists(RAGAS_PROGRESS_PATH):
        with open(RAGAS_PROGRESS_PATH, "r", encoding="utf-8") as f:
            all_results = json.load(f)
        print(f"Melanjutkan dari progress sebelumnya: {len(all_results)} pertanyaan sudah selesai\n")

    already_done = {r["question"] for r in all_results}

    for i, item in enumerate(enriched_items):
        if item["question"] in already_done:
            continue

        print(f"[{i+1}/{len(enriched_items)}] Evaluasi: {item['question']}")

        try:
            single_dataset = Dataset.from_list([item])
            result = evaluate(
                single_dataset,
                metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                llm=ragas_llm,
                embeddings=ragas_embeddings,
            )
            scores = result.to_pandas().iloc[0].to_dict()

            all_results.append({
                "question": item["question"],
                "answer": item["answer"],
                "scores": {
                    k: v for k, v in scores.items()
                    if k in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
                }
            })

            os.makedirs(os.path.dirname(RAGAS_PROGRESS_PATH), exist_ok=True)
            with open(RAGAS_PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)

            print(f"  -> Selesai: {all_results[-1]['scores']}")

        except Exception as e:
            print(f"  GAGAL: {e}")
            print("  Progress tersimpan sejauh ini. Jalankan ulang script untuk lanjut dari sini.")
            break  # hentikan loop, tapi progress yang sudah ada tetap aman

        time.sleep(DELAY_BETWEEN_QUESTIONS)

    return all_results


def calculate_average_scores(all_results: list) -> dict:
    """Hitung rata-rata tiap metrik secara manual dari semua hasil per-pertanyaan."""
    if not all_results:
        return {}

    metric_names = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    averages = {}

    for metric in metric_names:
        values = [r["scores"].get(metric) for r in all_results if r["scores"].get(metric) is not None]
        averages[metric] = round(sum(values) / len(values), 4) if values else None

    return averages


def save_final_results(all_results: list, averages: dict):
    output = {
        "aggregate_scores": averages,
        "total_questions_evaluated": len(all_results),
        "per_question_detail": all_results,
    }
    os.makedirs(os.path.dirname(EVAL_RESULTS_PATH), exist_ok=True)
    with open(EVAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    eval_items = load_eval_dataset()
    print(f"Total pertanyaan uji: {len(eval_items)}\n")

    enriched_items = run_pipeline_on_dataset(eval_items)

    print("\nMenghitung metrik RAGAS (satu per satu, dengan resume progress)...\n")
    all_results = run_ragas_one_by_one(enriched_items)

    averages = calculate_average_scores(all_results)

    print(f"\n=== HASIL EVALUASI RAGAS ({len(all_results)}/{len(enriched_items)} pertanyaan selesai) ===")
    for metric, value in averages.items():
        print(f"{metric}: {value}")

    save_final_results(all_results, averages)
    print(f"\nHasil lengkap disimpan di {EVAL_RESULTS_PATH}")

    if len(all_results) < len(enriched_items):
        print(f"\n⚠️  Belum semua pertanyaan selesai ({len(all_results)}/{len(enriched_items)}).")
        print("Jalankan ulang script ini untuk melanjutkan dari yang belum selesai.")