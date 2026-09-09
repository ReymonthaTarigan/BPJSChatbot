"""
llm_client.py
Wrapper untuk memanggil Groq API. Menyediakan 2 fungsi utama:
1. generate_answer() -> jawab pertanyaan user berdasarkan context
2. check_groundedness() -> verifikasi apakah jawaban didukung context
"""

import os
from groq import Groq
from dotenv import load_dotenv
from src.generation.prompts import (
    ANSWER_SYSTEM_PROMPT,
    build_answer_prompt,
    GROUNDEDNESS_SYSTEM_PROMPT,
    build_groundedness_prompt
)

load_dotenv()

MODEL_NAME = "openai/gpt-oss-120b"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_answer(query: str, context_chunks: list) -> str:
    """Panggil LLM untuk menjawab pertanyaan berdasarkan context."""
    user_prompt = build_answer_prompt(query, context_chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,  # rendah supaya jawaban lebih konsisten & tidak "kreatif"
    )

    return response.choices[0].message.content.strip()


def check_groundedness(context_chunks: list, answer: str) -> dict:
    """
    Verifikasi apakah jawaban didukung context.

    Returns:
        {"status": "YA"/"SEBAGIAN"/"TIDAK", "alasan": str}
    """
    user_prompt = build_groundedness_prompt(context_chunks, answer)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": GROUNDEDNESS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0,  # 0 supaya hasil verifikasi konsisten/deterministik
    )

    raw_output = response.choices[0].message.content.strip()

    # Parse output yang formatnya "STATUS: ...\nALASAN: ..."
    status = "TIDAK"  # default aman kalau parsing gagal
    alasan = raw_output

    for line in raw_output.split("\n"):
        if line.startswith("STATUS:"):
            status = line.replace("STATUS:", "").strip()
        elif line.startswith("ALASAN:"):
            alasan = line.replace("ALASAN:", "").strip()

    return {"status": status, "alasan": alasan}