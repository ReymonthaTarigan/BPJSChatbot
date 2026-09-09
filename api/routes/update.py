"""
update.py
Endpoint /update-data -- tombol "Update Data" di UI akan memanggil ini.
Alurnya: cek dulu halaman mana yang berubah (lewat Last-Modified header),
kalau ada yang berubah, scrape ulang HANYA halaman itu, lalu re-chunk
dan re-embed supaya ChromaDB selalu sinkron dengan data terbaru.
"""

from fastapi import APIRouter, HTTPException
from api.schemas import UpdateDataResponse
from src.scraper.update_checker import check_pages_need_update
from src.scraper.scraper import scrape_all_pages
from src.ingestion.chunker import build_chunks, save_chunks
from src.ingestion.embedder import embed_and_store

router = APIRouter()


@router.post("", response_model=UpdateDataResponse)
def update_data_endpoint():
    """
    Alur:
    1. Cek halaman mana yang Last-Modified-nya berubah
    2. Kalau tidak ada yang berubah -> selesai, tidak perlu proses apapun
    3. Kalau ada yang berubah -> scrape ulang SEMUA halaman (untuk simplisitas;
       lihat catatan di bawah soal kenapa bukan scrape parsial),
       lalu re-chunk dan re-embed ke ChromaDB
    """
    try:
        pages_to_update = check_pages_need_update()

        if not pages_to_update:
            return UpdateDataResponse(
                status="no_update_needed",
                pages_updated=[],
                message="Semua data sudah versi terbaru, tidak ada perubahan di sumber."
            )

        # Catatan: untuk simplisitas, kita scrape ULANG SEMUA halaman
        # (bukan cuma yang berubah), karena chunker.py memproses seluruh
        # isi data/raw/ sekaligus. Untuk skala 5 halaman, ini masih cepat
        # dan tidak masalah -- optimisasi scrape parsial bisa jadi
        # pengembangan lanjutan kalau jumlah halaman jauh lebih banyak.
        scrape_all_pages()

        chunks = build_chunks()
        save_chunks(chunks)
        embed_and_store(chunks)

        return UpdateDataResponse(
            status="success",
            pages_updated=pages_to_update,
            message=f"Berhasil update {len(pages_to_update)} halaman: {', '.join(pages_to_update)}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melakukan update: {str(e)}")