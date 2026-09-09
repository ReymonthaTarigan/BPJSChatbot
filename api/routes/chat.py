"""
chat.py
Endpoint /chat -- terima pertanyaan user, teruskan ke pipeline.ask(),
kembalikan jawaban dalam format yang sudah divalidasi Pydantic.
"""

from fastapi import APIRouter, HTTPException
from api.schemas import ChatRequest, ChatResponse, SourceInfo
from src.pipeline import ask

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Terima pertanyaan, jalankan pipeline RAG (retrieval + generation +
    groundedness check), kembalikan jawaban beserta metadata pendukung
    (sumber, confidence, status groundedness) untuk ditampilkan di UI.
    """
    try:
        result = ask(request.question)
    except Exception as e:
        # Kalau ada error tak terduga (misal Groq API down/rate limit),
        # kembalikan error yang jelas ke frontend, bukan crash diam-diam.
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")

    return ChatResponse(
        answer=result["answer"],
        sources=[
            SourceInfo(
                kategori=s["kategori"],
                judul=s["judul"],
                sumber_url=s["sumber_url"]
            )
            for s in result["sources"]
        ],
        confidence=result["confidence"],
        groundedness_status=result["groundedness_status"],
    )