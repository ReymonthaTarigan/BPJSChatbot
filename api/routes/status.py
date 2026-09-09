"""
status.py
Endpoint /status -- menampilkan info kondisi data saat ini: berapa
total chunk di database, kategori apa saja yang ada, dan kapan terakhir
kali dicek update-nya. Ini yang akan ditampilkan sebagai "freshness
indicator" di UI nanti (Fase 6).
"""

import json
import os
import chromadb
from fastapi import APIRouter
from api.schemas import StatusResponse

router = APIRouter()

VECTORSTORE_DIR = "vectorstore/chroma_db"
COLLECTION_NAME = "bpjs_panduan"
METADATA_PATH = "data/metadata.json"


@router.get("", response_model=StatusResponse)
def status_endpoint():
    """
    Ambil info status data saat ini:
    - Total chunk yang tersimpan di ChromaDB
    - Kategori apa saja yang ada
    - Isi metadata.json (kapan Last-Modified tiap halaman terakhir dicek)
    """
    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = collection.count()

    # Ambil semua metadata untuk tahu kategori apa saja yang ada
    all_data = collection.get(include=["metadatas"])
    categories = sorted(set(m["kategori"] for m in all_data["metadatas"]))

    # Baca metadata.json (hasil dari update_checker.py)
    metadata = {}
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return StatusResponse(
        total_chunks=total_chunks,
        categories=categories,
        last_update_check=None,  # bisa diisi dari file terpisah kalau mau tracking timestamp cek terakhir
        metadata=metadata
    )