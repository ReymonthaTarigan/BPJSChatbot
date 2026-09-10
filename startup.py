"""
startup.py
Dijalankan sekali saat server pertama kali start di container. Cek apakah
ChromaDB sudah punya data; kalau kosong (misal karena disk container
ter-reset setiap deploy baru), otomatis jalankan pipeline scraping ulang.
"""

import chromadb
from src.scraper.scraper import scrape_all_pages
from src.ingestion.chunker import build_chunks, save_chunks
from src.ingestion.embedder import embed_and_store

VECTORSTORE_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "bpjs_panduan"


def ensure_data_ready():
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() == 0:
        print("ChromaDB kosong, menjalankan pipeline data dari awal...")
        scrape_all_pages()
        chunks = build_chunks()
        save_chunks(chunks)
        embed_and_store(chunks)
        print("Pipeline data selesai.")
    else:
        print(f"ChromaDB sudah berisi {collection.count()} chunks, skip scraping.")


if __name__ == "__main__":
    ensure_data_ready()