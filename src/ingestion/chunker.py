"""
chunker.py
Mengubah data JSON hasil scraping (data/raw/*.json) jadi "chunks" siap embed.

Cara kerja:
- Baca semua file JSON di data/raw/
- Tiap "panduan" di dalamnya diubah jadi 1 chunk, dengan:
  - "text": gabungan judul + deskripsi + langkah dalam format natural,
             ini yang akan diubah jadi vector embedding
  - "metadata": info tambahan (kategori, sumber_url, judul) untuk citation nanti
  - "id": ID unik dan stabil, dipakai untuk update/replace di vector DB
"""

import json
import os
import glob
from typing import List, Dict

RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_PATH = "data/processed/chunks.json"


def format_chunk_text(panduan: Dict) -> str:
    """
    Gabungkan judul, deskripsi, dan langkah-langkah jadi 1 teks natural.
    Format ini yang akan diubah jadi embedding vector.

    Kenapa formatnya seperti ini (bukan JSON mentah)?
    Model embedding bekerja lebih baik dengan teks natural yang mengalir,
    karena dilatih dari teks bahasa manusia, bukan struktur data.
    """
    langkah_text = "\n".join(
        f"{i+1}. {langkah}" for i, langkah in enumerate(panduan["langkah"])
    )

    text = f"""Kategori: {panduan['kategori']}
Judul: {panduan['judul']}
Deskripsi: {panduan['deskripsi']}

Langkah-langkah:
{langkah_text}"""

    return text


def make_chunk_id(kategori_slug: str, index: int) -> str:
    """
    Buat ID unik dan STABIL untuk tiap chunk.

    Kenapa harus stabil (bukan random/UUID)?
    Supaya waktu data di-scrape ulang (tombol update), chunk lama dengan
    ID yang sama otomatis ter-REPLACE di vector DB, bukan numpuk jadi
    duplikat. ID dibuat dari kombinasi kategori + urutan panduan di
    halaman itu, yang polanya konsisten selama struktur web tidak berubah.
    """
    return f"{kategori_slug}-{index:03d}"


def load_all_raw_files() -> List[Dict]:
    """Baca semua file JSON hasil scraping di data/raw/."""
    raw_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    all_data = []

    for filepath in raw_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
            # simpan nama file (tanpa ekstensi) sebagai slug kategori untuk ID
            filename_slug = os.path.splitext(os.path.basename(filepath))[0]
            content["_filename_slug"] = filename_slug
            all_data.append(content)

    return all_data


def build_chunks() -> List[Dict]:
    """
    Proses utama: baca semua raw JSON, ubah tiap panduan jadi 1 chunk.

    Returns:
        List of dict, tiap dict:
        {
            "id": str,
            "text": str,          # siap di-embed
            "metadata": {
                "kategori": str,
                "judul": str,
                "sumber_url": str
            }
        }
    """
    all_raw_data = load_all_raw_files()
    chunks = []

    for file_content in all_raw_data:
        filename_slug = file_content["_filename_slug"]
        panduan_list = file_content.get("data", [])

        for idx, panduan in enumerate(panduan_list):
            chunk_id = make_chunk_id(filename_slug, idx)
            chunk_text = format_chunk_text(panduan)

            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "metadata": {
                     "id": chunk_id,
                    "kategori": panduan["kategori"],
                    "judul": panduan["judul"],
                    "sumber_url": panduan["sumber_url"]
                }
            })

    return chunks


def save_chunks(chunks: List[Dict]):
    """Simpan hasil chunking ke data/processed/chunks.json."""
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    with open(PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    chunks = build_chunks()
    save_chunks(chunks)
    print(f"Berhasil membuat {len(chunks)} chunks, disimpan di {PROCESSED_DATA_PATH}")

    # Tampilkan 1 contoh chunk supaya bisa langsung dicek
    if chunks:
        print("\n=== CONTOH CHUNK PERTAMA ===")
        print("ID:", chunks[0]["id"])
        print("Metadata:", chunks[0]["metadata"])
        print("\nText:")
        print(chunks[0]["text"])