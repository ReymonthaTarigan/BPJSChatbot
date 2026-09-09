"""
schemas.py
Model Pydantic untuk validasi request masuk dan bentuk response keluar
dari tiap endpoint API. FastAPI otomatis pakai ini untuk validasi dan
juga untuk generate dokumentasi API (Swagger UI).
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    """Body request yang dikirim frontend ke endpoint /chat."""
    question: str = Field(..., min_length=1, description="Pertanyaan dari user")


class SourceInfo(BaseModel):
    """Info sumber yang ditampilkan bersama jawaban (untuk citation)."""
    kategori: str
    judul: str
    sumber_url: str


class ChatResponse(BaseModel):
    """Response yang dikembalikan endpoint /chat ke frontend."""
    answer: str
    sources: List[SourceInfo]
    confidence: float
    groundedness_status: str


class UpdateDataResponse(BaseModel):
    """Response setelah proses update data (scraping ulang) selesai."""
    status: str  # "success" atau "no_update_needed" atau "failed"
    pages_updated: List[str]
    message: str


class StatusResponse(BaseModel):
    """Response untuk endpoint /status -- info kondisi data saat ini."""
    total_chunks: int
    categories: List[str]
    last_update_check: Optional[str] = None
    metadata: dict