"""
embedder.py
Mengubah chunks (dari chunker.py) jadi vector embeddings, lalu simpan
ke ChromaDB (vector database).

Cara kerja:
- Load chunks dari data/processed/chunks.json
- Pakai model SentenceTransformer multilingual untuk generate embedding
  tiap chunk (mengubah teks jadi vector angka yang merepresentasikan makna)
- Simpan ke ChromaDB, yang otomatis meng-index vector-vector ini supaya
  bisa dicari berdasarkan kemiripan makna (bukan cuma exact keyword match)
"""

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

PROCESSED_DATA_PATH = "data/processed/chunks.json"
VECTORSTORE_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "bpjs_panduan"

# Model embedding multilingual, ringan, jalan lokal (tidak perlu API key)
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def load_chunks() -> List[Dict]:
    """Baca hasil chunking dari data/processed/chunks.json."""
    with open(PROCESSED_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_chroma_collection():
    """
    Buat/ambil koneksi ke ChromaDB collection.

    PersistentClient artinya data disimpan permanen di disk
    (folder vectorstore/chroma_db/), bukan cuma di memory —
    jadi tidak hilang tiap kali program di-restart.
    """
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
        )
    return collection


def embed_and_store(chunks: List[Dict]):
    """
    Generate embedding untuk semua chunks, simpan ke ChromaDB.

    Menggunakan collection.upsert() (bukan .add()) supaya kalau chunk
    dengan ID yang sama sudah ada (dari scraping sebelumnya), otomatis
    di-REPLACE dengan versi terbaru -- ini yang membuat fitur "tombol
    update" bekerja tanpa menyebabkan data duplikat menumpuk.
    """
    print(f"Loading model embedding: {EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    collection = get_chroma_collection()

    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    print(f"Generating embeddings untuk {len(texts)} chunks ...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    print("Menyimpan ke ChromaDB ...")
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"Selesai. Total chunks di collection sekarang: {collection.count()}")


if __name__ == "__main__":
    chunks = load_chunks()
    embed_and_store(chunks)