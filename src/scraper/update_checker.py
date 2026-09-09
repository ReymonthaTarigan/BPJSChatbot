"""
update_checker.py
Mengecek apakah halaman BPJS punya versi baru dibanding data yang sudah 
tersimpan, tanpa perlu download & parse ulang seluruh halaman.

Cara kerja:
- Kirim request HEAD (bukan GET) ke tiap URL -> jauh lebih cepat & ringan
  karena tidak download body HTML, cuma ambil header
- Bandingkan header 'Last-Modified' dengan yang tersimpan di data/metadata.json
- Kalau beda -> tandai halaman itu perlu di-scrape ulang
"""

import requests
import json
import os
from src.scraper.scraper import TARGET_PAGES, HEADERS

METADATA_PATH = "data/metadata.json"


def load_metadata() -> dict:
    """Baca metadata tersimpan (last_modified per halaman)."""
    if not os.path.exists(METADATA_PATH):
        return {}
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(metadata: dict):
    """Simpan metadata terbaru."""
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def check_pages_need_update() -> list:
    """
    Cek semua halaman target, return list nama_file yang perlu di-update
    (karena Last-Modified berubah atau belum pernah di-scrape sama sekali).
    """
    old_metadata = load_metadata()
    new_metadata = {}
    pages_to_update = []

    for kategori, url, filename in TARGET_PAGES:
        try:
            response = requests.head(url, headers=HEADERS, timeout=10)
            current_last_modified = response.headers.get("Last-Modified", "")
            new_metadata[filename] = current_last_modified

            old_last_modified = old_metadata.get(filename, None)

            if old_last_modified != current_last_modified:
                pages_to_update.append(filename)
                print(f"[UPDATE PERLU] {kategori}: {old_last_modified} -> {current_last_modified}")
            else:
                print(f"[SUDAH TERBARU] {kategori}")

        except Exception as e:
            print(f"[ERROR CEK] {kategori}: {e}")
            # Kalau gagal cek, aman-nya anggap perlu di-update
            pages_to_update.append(filename)

    save_metadata(new_metadata)
    return pages_to_update


if __name__ == "__main__":
    pages = check_pages_need_update()
    print(f"\nHalaman yang perlu di-update: {pages if pages else 'tidak ada'}")