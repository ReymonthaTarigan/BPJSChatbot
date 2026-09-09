"""
check_retrieval_accuracy.py
Menghitung Recall@K (Hit Rate@K): dari semua pertanyaan uji, berapa
persen yang chunk seharusnya (expected_chunk_id) berhasil ditemukan
sistem retrieval dalam top-K hasil.

Ini metrik OBJEKTIF (exact match), tidak melibatkan LLM sama sekali --
beda dengan RAGAS yang pakai LLM-as-judge.
"""

import json
from src.retrieval.retriever import Retriever, TOP_K

EVAL_DATASET_PATH = "data/eval/eval_dataset.json"


def load_eval_dataset() -> list:
    with open(EVAL_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_recall_at_k(retriever: Retriever, eval_items: list, k: int = TOP_K) -> dict:
    """
    Untuk tiap pertanyaan, cek apakah expected_chunk_id muncul di top-k
    hasil retrieval. Return detail per-pertanyaan + skor agregat.
    """
    results = []
    hits = 0

    for item in eval_items:
        question = item["question"]
        expected_id = item.get("expected_chunk_id")

        if not expected_id:
            print(f"[SKIP] Tidak ada expected_chunk_id untuk: {question}")
            continue

        retrieval_result = retriever.retrieve(question, top_k=k)
        retrieved_ids = [c["metadata"].get("id") for c in retrieval_result["chunks"]]

        # Karena metadata chunk saat ini belum simpan "id" chunk itu sendiri,
        # kita cocokkan pakai judul sebagai pengganti sementara 
        is_hit = expected_id in retrieved_ids

        results.append({
            "question": question,
            "expected_chunk_id": expected_id,
            "retrieved_ids": retrieved_ids,
            "hit": is_hit
        })

        if is_hit:
            hits += 1

    total = len(results)
    recall_at_k = hits / total if total > 0 else 0

    return {
        "recall_at_k": round(recall_at_k, 4),
        "hits": hits,
        "total": total,
        "k": k,
        "detail": results
    }


if __name__ == "__main__":
    eval_items = load_eval_dataset()
    retriever = Retriever()

    result = calculate_recall_at_k(retriever, eval_items)

    print(f"\n=== RECALL@{result['k']} ===")
    print(f"Hits: {result['hits']}/{result['total']} ({result['recall_at_k']*100:.1f}%)\n")

    for d in result["detail"]:
        status = "✅ HIT" if d["hit"] else "❌ MISS"
        print(f"{status} | Q: {d['question']}")
        print(f"   Expected: {d['expected_chunk_id']}")
        print(f"   Retrieved: {d['retrieved_ids']}\n")