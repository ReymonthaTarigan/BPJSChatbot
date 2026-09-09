"""
scraper.py
Mengambil HTML dari 6 halaman BPJS, lalu memanggil parser.py untuk 
mengubahnya jadi JSON, dan menyimpannya ke data/raw/.

Cara kerja:
- List semua URL target beserta nama kategorinya
- Untuk tiap URL: request HTML -> parse -> simpan JSON per kategori
- Pakai header User-Agent supaya request terlihat seperti browser biasa
  (bukan wajib di sini karena halaman file .html statis ini tidak diblokir WAF,
  tapi ini praktik baik untuk scraping secara umum)
"""

import requests
import json
import os
from datetime import datetime, timezone
from src.scraper.parser import parse_panduan_page

# Daftar halaman target: (kategori, url, nama_file_output)
TARGET_PAGES = [
    ("Akun Mobile JKN", "https://bpjs-kesehatan.go.id/user-manual-mobile-jkn/akun-mobile-jkn.html", "akun-mobile-jkn"),
    ("Administrasi JKN", "https://bpjs-kesehatan.go.id/user-manual-mobile-jkn/administrasi%20JKN.html", "administrasi-jkn"),
    ("Pelayanan JKN", "https://bpjs-kesehatan.go.id/user-manual-mobile-jkn/pelayanan%20jkn.html", "pelayanan-jkn"),
    ("Iuran Kepesertaan", "https://bpjs-kesehatan.go.id/user-manual-mobile-jkn/iuran%20kepesertaan.html", "iuran-kepesertaan"),
    ("Lain-lain", "https://bpjs-kesehatan.go.id/user-manual-mobile-jkn/lain-lain.html", "lain-lain"),
]
# video_mjkn.html sengaja tidak dimasukkan dulu karena isinya kemungkinan cuma
# link video, bukan teks instruksi -> perlu ditangani terpisah nanti.

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

RAW_DATA_DIR = "data/raw"


def fetch_page(url: str) -> requests.Response:
    """Ambil HTML dari 1 URL, raise error kalau gagal."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()  # akan raise exception kalau status code error
    return response


def scrape_all_pages() -> dict:
    """
    Scrape semua halaman target, simpan tiap hasil sebagai JSON terpisah
    di data/raw/, dan return summary hasil scraping.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    summary = {}

    for kategori, url, filename in TARGET_PAGES:
        print(f"Scraping: {kategori} ({url})")
        try:
            response = fetch_page(url)
            panduan_list = parse_panduan_page(response.text, url, kategori)

            output = {
                "kategori": kategori,
                "sumber_url": url,
                "last_modified_header": response.headers.get("Last-Modified", ""),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "jumlah_panduan": len(panduan_list),
                "data": panduan_list
            }

            filepath = os.path.join(RAW_DATA_DIR, f"{filename}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            summary[filename] = {
                "status": "success",
                "jumlah_panduan": len(panduan_list)
            }
            print(f"  -> berhasil, {len(panduan_list)} panduan ditemukan")

        except Exception as e:
            summary[filename] = {"status": "failed", "error": str(e)}
            print(f"  -> GAGAL: {e}")

    return summary


if __name__ == "__main__":
    result = scrape_all_pages()
    print("\n=== RINGKASAN SCRAPING ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))