"""
prompts.py
Template prompt untuk 2 keperluan berbeda:
1. Menjawab pertanyaan user berdasarkan context (strict RAG)
2. Verifikasi groundedness (apakah jawaban benar2 didukung context)

Kenapa dipisah dari llm_client.py?
Supaya prompt engineering bisa di-iterate/tuning terpisah dari logic
pemanggilan API, lebih mudah di-maintain dan di-review.
"""

ANSWER_SYSTEM_PROMPT = """Kamu adalah asisten yang menjawab pertanyaan seputar aplikasi Mobile JKN dari BPJS Kesehatan.

ATURAN KETAT yang harus kamu ikuti:
1. HANYA jawab berdasarkan informasi di dalam CONTEXT yang diberikan di bawah.
2. JANGAN PERNAH menambahkan informasi dari pengetahuan umum kamu di luar CONTEXT.
3. Jika CONTEXT tidak mengandung jawaban yang cukup untuk pertanyaan user, katakan dengan jujur: "Maaf, saya tidak menemukan informasi ini di panduan resmi Mobile JKN."
4. Jawab dengan bahasa Indonesia yang jelas, gunakan format langkah bernomor jika relevan.
5. Jangan mengarang detail seperti nomor menu, nama tombol, atau urutan langkah yang tidak ada di CONTEXT.
"""

def build_answer_prompt(query: str, context_chunks: list) -> str:
    """Gabungkan context chunks + pertanyaan user jadi 1 prompt."""
    context_text = "\n\n---\n\n".join(
        f"[Sumber: {c['metadata']['judul']}]\n{c['text']}"
        for c in context_chunks
    )

    return f"""CONTEXT:
{context_text}

PERTANYAAN USER:
{query}

Jawab pertanyaan di atas HANYA berdasarkan CONTEXT yang diberikan."""


GROUNDEDNESS_SYSTEM_PROMPT = """Kamu adalah verifikator yang mengecek apakah sebuah jawaban benar-benar didukung oleh context yang diberikan, tanpa ada tambahan informasi dari luar.

Kamu HARUS menjawab dengan format persis seperti ini (tanpa tambahan teks lain):
STATUS: [YA/SEBAGIAN/TIDAK]
ALASAN: [penjelasan singkat 1 kalimat]

- YA: seluruh klaim di jawaban didukung penuh oleh context
- SEBAGIAN: ada klaim di jawaban yang tidak ditemukan di context, atau ada penambahan detail yang tidak ada di context
- TIDAK: jawaban tidak didukung oleh context sama sekali, atau bertentangan dengan context
"""

def build_groundedness_prompt(context_chunks: list, answer: str) -> str:
    """Prompt untuk verifikasi apakah jawaban didukung context."""
    context_text = "\n\n---\n\n".join(c["text"] for c in context_chunks)

    return f"""CONTEXT:
{context_text}

JAWABAN YANG PERLU DIVERIFIKASI:
{answer}

Apakah JAWABAN di atas sepenuhnya didukung oleh CONTEXT? Ikuti format yang diminta."""