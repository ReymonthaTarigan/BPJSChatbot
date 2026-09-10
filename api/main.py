"""
main.py
Entrypoint utama FastAPI. Menggabungkan semua router (chat, update, status)
jadi 1 aplikasi, plus konfigurasi CORS supaya bisa diakses dari frontend
yang jalan di port/domain berbeda (misal React dev server di localhost:5173).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, update, status

app = FastAPI(
    title="BPJS Mobile JKN Chatbot API",
    description="API untuk chatbot panduan Mobile JKN dengan RAG + anti-halusinasi",
    version="1.0.0",
)

# CORS: mengizinkan frontend (domain/port berbeda) memanggil API ini.
# Untuk development, kita izinkan semua origin ("*"). Untuk production,
# sebaiknya diganti ke domain frontend yang spesifik saja.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Daftarkan semua router
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(update.router, prefix="/update-data", tags=["Update"])
app.include_router(status.router, prefix="/status", tags=["Status"])


@app.get("/")
def root():
    """Endpoint root, cuma untuk cek API hidup atau tidak."""
    return {"message": "BPJS Mobile JKN Chatbot API is running"}