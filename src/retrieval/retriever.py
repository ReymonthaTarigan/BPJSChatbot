"""
retriever.py
Mencari chunk paling relevan dari ChromaDB berdasarkan pertanyaan user,
plus menerapkan similarity threshold sebagai gate pertama anti-halusinasi.

Cara kerja:
- Ubah pertanyaan user jadi embedding (pakai model yang SAMA dengan
  yang dipakai waktu embedding data, supaya vector-nya "sepadan")
- Query ChromaDB, ambil N chunk paling mirip
- ChromaDB return "distance" (semakin kecil = semakin mirip), kita ubah
  jadi "similarity score" yang lebih intuitif (semakin besar = semakin mirip)
- Kalau similarity tertinggi di bawah threshold -> anggap tidak ada
  jawaban relevan, jangan lanjut ke LLM sama sekali (hemat API call
  DAN mencegah LLM "terpaksa mengarang" dari konteks yang tidak nyambung)
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

VECTORSTORE_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "bpjs_panduan"
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Threshold ini hasil eksperimen, bisa disesuaikan setelah testing.
# Similarity score berkisar 0-1 (1 = identik, 0 = tidak mirip sama sekali).
SIMILARITY_THRESHOLD = 0.35

TOP_K = 3  # ambil 3 chunk paling relevan


class Retriever:
    def __init__(self):
        print("Loading embedding model untuk retrieval...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
        self.collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
            )

    def retrieve(self, query: str, top_k: int = TOP_K) -> Dict:
        """
        Cari chunk paling relevan untuk 1 pertanyaan.

        Returns:
            {
                "has_relevant_context": bool,
                "chunks": List[Dict],   # tiap dict: {text, metadata, similarity}
                "top_similarity": float
            }
        """
        query_embedding = self.model.encode([query]).tolist()

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )

        # ChromaDB return "distance" (cosine distance), semakin kecil
        # semakin mirip. Kita ubah jadi similarity score: 1 - distance
        # supaya lebih intuitif (semakin besar = semakin relevan).
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        chunks = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1 - dist
            chunks.append({
                "text": doc,
                "metadata": meta,
                "similarity": round(similarity, 4)
            })

        top_similarity = chunks[0]["similarity"] if chunks else 0.0
        has_relevant_context = top_similarity >= SIMILARITY_THRESHOLD

        return {
            "has_relevant_context": has_relevant_context,
            "chunks": chunks,
            "top_similarity": top_similarity
        }


if __name__ == "__main__":
    # Test manual
    retriever = Retriever()

    test_queries = [
        "Bagaimana cara mendaftar jadi peserta JKN?",
        "Cara ganti nama presiden Indonesia",  # pertanyaan di luar topik, untuk test gate
    ]

    for q in test_queries:
        print(f"\n=== Query: {q} ===")
        result = retriever.retrieve(q)
        print(f"Top similarity: {result['top_similarity']}")
        print(f"Has relevant context: {result['has_relevant_context']}")
        for c in result["chunks"]:
            print(f"  - [{c['similarity']}] {c['metadata']['judul']}")