"""
pipeline.py
Orchestrator utama: menyatukan retrieval -> generation -> groundedness check
jadi 1 fungsi ask() yang siap dipanggil dari API backend.
"""

from src.retrieval.retriever import Retriever
from src.generation.llm_client import generate_answer, check_groundedness

retriever = Retriever()


def ask(query: str) -> dict:
    """
    Fungsi utama chatbot. Alur:
    1. Retrieve chunk relevan
    2. Kalau tidak ada yang relevan (similarity rendah) -> jawab "tidak tahu"
       TANPA panggil LLM sama sekali
    3. Kalau ada -> generate jawaban dari LLM
    4. Verifikasi groundedness jawaban tsb
    5. Kalau groundedness gagal (SEBAGIAN/TIDAK) -> ganti jawaban jadi
       fallback message, JANGAN tampilkan jawaban yang tidak terverifikasi

    Returns:
        {
            "answer": str,
            "sources": List[dict],
            "confidence": float,
            "groundedness_status": str
        }
    """
    # --- Lapis 1: Retrieval Gate ---
    retrieval_result = retriever.retrieve(query)

    if not retrieval_result["has_relevant_context"]:
        return {
            "answer": "Maaf, saya tidak menemukan informasi ini di panduan resmi Mobile JKN. Silakan cek langsung di aplikasi atau hubungi layanan BPJS Kesehatan.",
            "sources": [],
            "sources_full": [],
            "confidence": retrieval_result["top_similarity"],
            "groundedness_status": "N/A (tidak ada context relevan)"
        }

    context_chunks = retrieval_result["chunks"]

    # --- Generation ---
    answer = generate_answer(query, context_chunks)

    # --- Lapis 2: Groundedness Check ---
    groundedness = check_groundedness(context_chunks, answer)

    if groundedness["status"] in ["SEBAGIAN", "TIDAK"]:
        return {
            "answer": "Maaf, saya tidak yakin dengan jawaban untuk pertanyaan ini. Silakan cek panduan resmi Mobile JKN secara langsung.",
            "sources": [c["metadata"] for c in context_chunks],
            "sources_full": context_chunks,
            "confidence": retrieval_result["top_similarity"],
            "groundedness_status": f"{groundedness['status']} - {groundedness['alasan']}"
        }

    return {
        "answer": answer,
        "sources": [c["metadata"] for c in context_chunks],
        "sources_full": context_chunks,  
        "confidence": retrieval_result["top_similarity"],
        "groundedness_status": groundedness["status"]
    }


if __name__ == "__main__":
    test_queries = [
        "Bagaimana cara mendaftar jadi peserta JKN?",
        "Siapa presiden Indonesia sekarang?",
    ]

    for q in test_queries:
        print(f"\n{'='*50}")
        print(f"Q: {q}")
        result = ask(q)
        print(f"A: {result['answer']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Groundedness: {result['groundedness_status']}")
        print(f"Sources: {[s['judul'] for s in result['sources']]}")