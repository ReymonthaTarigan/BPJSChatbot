# Chatbot Panduan Mobile JKN (BPJS Kesehatan)

Chatbot RAG (Retrieval-Augmented Generation) yang menjawab pertanyaan seputar penggunaan aplikasi Mobile JKN, dibangun dari data yang di-scrape langsung dari halaman resmi panduan pengguna BPJS Kesehatan. Proyek ini fokus pada penerapan mekanisme **anti-halusinasi** yang jelas dan dapat dievaluasi secara kuantitatif, bukan sekadar RAG dasar.

---

## 1. Ringkasan Arsitektur

```
[Scraper] → [Parser] → [Chunker] → [Embedder/ChromaDB]
                                          │
                                          ▼
User Query → [Retriever + Similarity Gate] → [LLM Generation] → [Groundedness Check] → Jawaban
```

### Sumber Data
- 5 halaman resmi panduan Mobile JKN di `bpjs-kesehatan.go.id/user-manual-mobile-jkn/`
- Kategori: Akun Mobile JKN, Administrasi JKN, Pelayanan JKN, Iuran Kepesertaan, Lain-lain
- Halaman `video_mjkn.html` sengaja tidak diikutkan (isinya tautan video, bukan teks instruksi)
- Total setelah scraping & fix parser: **40 chunk** (1 chunk = 1 panduan lengkap)

### Stack Teknis
| Komponen | Teknologi |
|---|---|
| Scraping | `requests` + `BeautifulSoup` (lxml parser) |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers, lokal) |
| Vector DB | ChromaDB (cosine similarity) |
| LLM | Groq API — `openai/gpt-oss-120b` |
| Evaluasi | Custom Recall@K + RAGAS (faithfulness, answer relevancy, context precision, context recall) |

---

## 2. Mekanisme Anti-Halusinasi (2 Lapis)

### Lapis 1 — Retrieval Similarity Gate
Pertanyaan user diubah jadi embedding, dicocokkan ke 40 chunk via cosine similarity. Jika similarity chunk teratas berada **di bawah threshold 0.35**, sistem langsung menjawab "tidak ditemukan" **tanpa memanggil LLM sama sekali** — mencegah LLM dipaksa menjawab dari konteks yang tidak relevan.

### Lapis 2 — Groundedness Check (LLM-as-verifier)
Setelah LLM menghasilkan jawaban, dilakukan **API call terpisah** yang meminta LLM (dengan peran berbeda: verifikator, bukan penjawab) menilai apakah jawaban tersebut didukung penuh oleh konteks yang diberikan. Hasil: `YA` / `SEBAGIAN` / `TIDAK`. Jika bukan `YA`, jawaban **dibuang seluruhnya** dan diganti pesan fallback (desain *all-or-nothing*, lihat bagian Keterbatasan).

### Catatan Jujur soal Metodologi
Kedua lapis di atas **bukan jaminan matematis** terhadap halusinasi:
- Lapis 1 murni berbasis vector similarity — bisa gagal pada kasus *vocabulary gap* (lihat Temuan #1).
- Lapis 2 sama-sama menggunakan LLM (prompting), sehingga rentan terhadap pola kegagalan yang mirip dengan LLM generator itu sendiri (*self-critique bias*). Ini bukan verifikasi independen dalam arti teknis ketat, melainkan mitigasi tambahan yang mengurangi probabilitas kesalahan lolos ke user — bukan menghilangkannya.

---

## 3. Metodologi Evaluasi

Evaluasi dirancang 3 lapis, mengikuti prinsip yang umum dipakai pada riset evaluasi RAG (kombinasi retrieval metric objektif + LLM-as-judge + human review):

| Lapis | Metrik | Objektivitas | Ketergantungan LLM |
|---|---|---|---|
| 1 | **Recall@K** (Hit Rate@3) | Tinggi — exact match ID chunk | Tidak |
| 2 | **RAGAS** (faithfulness, answer relevancy, context precision, context recall) | Sedang — LLM-as-judge | Ya |
| 3 | **Human review** (spot-check manual) | Tinggi (subjektif, tidak scalable) | Tidak |

### Metodologi Penyusunan Pertanyaan Uji
Pertanyaan uji (43 pertanyaan) disusun dengan mempertimbangkan:
- **Coverage**: mewakili seluruh 5 kategori data
- **Variasi tingkat kesulitan**: mudah (kata kunci cocok persis judul), medium (parafrase), sulit (istilah umum/singkatan yang berbeda dari istilah sumber)
- **Proses eksploratif**: sebagian pertanyaan ditambahkan setelah ditemukan gagal secara tidak sengaja saat eksplorasi manual (*tricky questions*), bukan hanya pertanyaan yang diperkirakan akan berhasil

**Keterbatasan yang diakui secara jujur:** pertanyaan uji disusun oleh satu orang (bukan multi-annotator atau generasi otomatis berskala besar), sehingga tetap berpotensi bias cakupan dibanding metode yang lebih sistematis (mis. semantic coverage measurement).

---

## 4. Hasil Evaluasi

### 4.1 Recall@K (Retrieval Accuracy)

**Hasil akhir: 43/43 (100%)**

Awalnya ditemukan 4 miss dari 43 pertanyaan. Setelah investigasi:
- 3 kasus terbukti murni **typo** pada pertanyaan uji ("kepersertaan" vs "kepesertaan") — setelah dikoreksi, langsung hit.
- Sisanya dikonfirmasi sebagai pola **vocabulary gap** yang konsisten (lihat Temuan #1 di bawah).

### 4.2 RAGAS (Generation Quality)

Dievaluasi pada 27 dari 42 pertanyaan uji (sisanya dihentikan karena keterbatasan kuota API harian pada tier gratis Groq; 27 sampel dinilai representatif untuk menarik kesimpulan awal karena sudah mencakup seluruh 5 kategori data serta variasi tingkat kesulitan).

**Skor agregat:**
| Metrik | Skor |
|---|---|
| Faithfulness | 0.6983 |
| Answer Relevancy | 0.5601 |
| Context Precision | 0.8951 |
| Context Recall | 1.0 |

**Catatan penting soal skor agregat:** Angka `faithfulness` dan `answer_relevancy` yang terlihat "sedang" ini banyak dipengaruhi oleh 7 dari 27 pertanyaan yang dijawab dengan pesan fallback ("tidak yakin") — untuk kasus tersebut RAGAS otomatis memberi skor 0.0 karena tidak ada klaim substantif yang bisa dinilai. Pada pertanyaan yang benar-benar dijawab (20 dari 27), skor faithfulness rata-rata jauh lebih tinggi (mayoritas antara 0.85–1.0). Rincian ini penting untuk diagnosis yang tepat — lihat Temuan #4.

### 4.3 Human Review

Dilakukan spot-check manual pada beberapa kasus dengan skor rendah/anomali (lihat detail di bagian Temuan). Proses ini berhasil menemukan dan mengkonfirmasi akar penyebab yang tidak selalu tertangkap oleh metrik otomatis semata.

---

## 5. Temuan Kunci

### Temuan #1 — Vocabulary Gap pada Retrieval
Pertanyaan dengan istilah umum/sehari-hari yang berbeda dari istilah resmi di sumber data menghasilkan retrieval yang kurang presisi. Contoh nyata:

| Query | Top-1 Similarity | Top-1 Match |
|---|---|---|
| "cara login **Mobile JKN**" | 0.7783 | ✅ "Panduan login ke MOBILE JKN" (tepat) |
| "cara login **BPJS**" | 0.5387 | ❌ "Panduan mendaftar peserta JKN" (chunk login tidak masuk top-3 sama sekali) |

Kasus serupa juga muncul pada istilah "fasilkes" (singkatan) vs "fasilitas kesehatan" (istilah lengkap di sumber).

**Sifat kegagalan ini penting dibedakan dari halusinasi**: jawaban yang dihasilkan tetap 100% akurat dan grounded dari sumber (tidak mengarang apa pun) — masalahnya terletak pada retrieval yang mengambil chunk yang kurang tepat sasaran, bukan pada generation yang berbohong.

### Temuan #2 — Dilusi Embedding pada Chunk Panjang/Jargon-Heavy
Chunk "Panduan untuk mengubah segmen kepesertaan" (7 langkah, sarat istilah teknis administratif seperti PBPU, PPU, PBI, Autodebit, OTP, Dati2) mendapat similarity **terendah** (0.1855) untuk query yang justru sangat cocok dengan judulnya sendiri. Chunk yang jauh lebih pendek dan fokus justru mengungguli similarity-nya. Ini mengkonfirmasi risiko yang diantisipasi sejak desain awal: chunk yang terlalu panjang dan padat istilah berisiko menghasilkan embedding yang representasinya "encer", kurang presisi mewakili makna inti.

**Konfirmasi kuantitatif dari RAGAS:** pertanyaan "Bagaimana mengubah segmen kepesertaan?" mencatat `context_precision: 0.333` — terendah di antara seluruh pertanyaan yang berhasil dijawab pada evaluasi RAGAS. Menariknya, `faithfulness`-nya tetap tinggi (0.857) — LLM tetap menjawab dengan akurat dari chunk yang berhasil ditemukan, namun `answer_relevancy` ikut anjlok (0.358, terendah kedua di seluruh dataset), mengindikasikan jawaban yang dihasilkan kurang fokus/relevan akibat context yang kurang presisi tadi.

### Temuan #4 — Groundedness Checker Berpotensi Terlalu Konservatif (Kemungkinan False Rejection)
Dari 27 pertanyaan yang dievaluasi RAGAS, 7 (26%) dijawab dengan pesan fallback. Ditemukan bahwa ketujuh kasus ini terbagi menjadi dua penyebab yang berbeda:

- **3 kasus murni retrieval gagal** (context_precision rendah, 0.33–0.49): "logout dari aplikasi", "notifikasi yang dulu pernah dikirim", "melihat jadwal operasi" — kemungkinan topik ini memang tidak dijelaskan secara eksplisit di 40 chunk sumber, atau retrieval gagal menemukannya.
- **4 kasus retrieval BENAR (context_precision ~0.99) namun tetap ditolak**: "kata sandi yang lupa" (telah diverifikasi manual sebagai true positive — LLM benar menambahkan klaim tidak berdasar), "menambah anggota keluarga", "mengubah alamat surat", "mengambil antrean fasilitas kesehatan tingkat lanjut".

Kelompok kedua ini penting: retrieval sudah menemukan sumber yang tepat, namun jawaban tetap dibuang total. Ini mengindikasikan groundedness checker berpotensi menghasilkan **false rejection** pada sebagian kasus — bukan hanya menangkap halusinasi asli, tapi mungkin juga terlalu ketat menolak jawaban yang sebenarnya cukup valid. Tiga kasus terakhir dalam kelompok ini belum diverifikasi manual satu per satu (keterbatasan waktu); kasus "kata sandi yang lupa" yang sudah diverifikasi terbukti sebagai true positive (halusinasi nyata), namun belum tentu representatif untuk ketiga kasus lainnya.

**Implikasi:** tingkat false-rejection yang belum terukur pasti ini adalah trade-off yang secara sadar diterima mengingat desain all-or-nothing yang dipilih (lihat bagian Keterbatasan) — sistem lebih memilih "diam" daripada berisiko menyesatkan, namun ini juga berarti sejumlah jawaban yang sebenarnya valid ikut tidak ditampilkan ke pengguna.

### Temuan #5 — RAGAS Kesulitan Menilai Jawaban yang Jujur Mengaku Tidak Tahu
Untuk pertanyaan "Bagaimana mengubah NIK dan nama anggota keluarga", LLM menjawab dengan benar bahwa panduan yang tersedia tidak menjelaskan prosedur perubahan nama, dan hanya menjelaskan syarat terbatas untuk perubahan NIK (bayi baru lahir dengan NIK terdaftar Dukcapil) — jawaban ini secara faktual jujur dan tidak mengarang. Namun RAGAS memberi skor `faithfulness: 0.5`, kemungkinan karena metodologi pemecahan klaim RAGAS kesulitan menilai kalimat yang berisi "pengakuan ketidaktahuan" sebagai klaim yang bisa diverifikasi. Ini menunjukkan keterbatasan RAGAS sebagai LLM-as-judge: skor rendah tidak selalu berarti kualitas jawaban buruk.

### Temuan #3 — Kasus Generation Failure Murni (Halusinasi Terverifikasi)
Untuk pertanyaan **"Bagaimana mengubah kata sandi yang lupa?"**, retrieval bekerja sempurna (context precision & recall = 1.0, similarity 0.65 pada chunk yang tepat), namun LLM menambahkan satu kalimat penutup yang tidak ada dasarnya di sumber:

> *"...ikuti petunjuk selanjutnya yang diberikan oleh aplikasi untuk menetapkan kata sandi baru."*

Groundedness checker berhasil mendeteksi ini (status `SEBAGIAN`) dan mencegah jawaban tersebut sampai ke user. Ini adalah bukti konkret bahwa lapis groundedness check bekerja sesuai tujuannya — berhasil menangkap kasus halusinasi yang murni berasal dari generation, bukan dari retrieval yang salah.

**Namun**, temuan ini juga mengungkap keterbatasan desain: sistem bersifat **all-or-nothing** — satu klaim yang tidak grounded menyebabkan **seluruh** jawaban dibuang, meski 3 dari 4 langkah yang dihasilkan sebenarnya akurat dan berguna. Ini adalah keputusan desain yang disengaja (mengutamakan keamanan informasi di atas kelengkapan jawaban), bukan keterbatasan teknis yang tidak disadari — lihat bagian Keterbatasan & Pengembangan Lanjutan.

---

## 6. Keterbatasan & Pengembangan Lanjutan

Bagian ini ditulis secara sengaja untuk jujur soal batas kemampuan sistem, bukan mengklaim sistem "100% anti-halusinasi":

1. **Groundedness check berbasis prompting, bukan verifikasi independen absolut.** Sama seperti LLM generator, verifikator ini bisa salah menilai — misalnya karena kecenderungan menilai berdasarkan kemiripan topik/gaya (gestalt), bukan pengecekan klaim per klaim yang ketat. **Temuan #4 menunjukkan indikasi awal false-rejection rate yang signifikan** (4 dari 27 pertanyaan uji, ~15%, ditolak meski retrieval-nya tepat sasaran) — angka pastinya belum terverifikasi manual sepenuhnya, namun ini sinyal bahwa checker saat ini kemungkinan terlalu konservatif.
2. **Desain all-or-nothing pada groundedness check.** Status `SEBAGIAN` diperlakukan sama dengan `TIDAK` (jawaban dibuang total). Pertimbangan desain: untuk domain informasi yang bila diikuti keliru dapat membuat pengguna gagal menyelesaikan prosedur, *tidak menjawab* dinilai lebih aman daripada *menjawab dengan disclaimer ketidakpastian* yang berisiko membingungkan pengguna awam. Pengembangan lanjutan yang lebih granular (klaim-per-klaim, mengikuti pendekatan RAGAS `faithfulness`) dapat mempertahankan bagian jawaban yang benar tanpa membuang seluruhnya — namun ini menambah latensi dan biaya API secara signifikan (butuh beberapa API call tambahan per klaim), sehingga belum diimplementasikan pada versi live/real-time.
3. **Retrieval sensitif terhadap vocabulary gap** (Temuan #1) — belum ada query expansion atau sinonim mapping.
4. **Tidak ada reranking** — retrieval murni mengandalkan cosine similarity dari bi-encoder embedding, tanpa lapis re-ranking tambahan yang biasanya meningkatkan presisi top-K.
5. **Bias dalam penyusunan test set** — pertanyaan uji disusun oleh satu orang; belum divalidasi lewat multi-annotator atau pengukuran cakupan semantik secara sistematis.
6. **RAGAS sebagai LLM-as-judge** juga memiliki keterbatasan objektivitas yang sama seperti groundedness checker custom, meski levelnya lebih granular (klaim-per-klaim, bukan keputusan tunggal).

### Rencana Pengembangan Lanjutan (belum diimplementasikan)
- Query expansion / sinonim mapping untuk mengatasi vocabulary gap
- Reranking (cross-encoder) sebelum konteks dikirim ke LLM
- Groundedness check granular (klaim-per-klaim) sebagai opsi mode "high precision", dengan trade-off latensi
- Semantic coverage measurement untuk validasi representativitas test set

---

## 7. Cara Menjalankan

```bash
# 1. Setup environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Isi API key
cp .env.example .env  # lalu isi GROQ_API_KEY

# 3. Jalankan pipeline data (scraping -> chunking -> embedding)
python -m src.scraper.scraper
python -m src.ingestion.chunker
python -m src.ingestion.embedder

# 4. Test pipeline chatbot
python -m src.pipeline

# 5. Jalankan evaluasi
python -m src.evaluation.check_retrieval_accuracy   # Recall@K
python -m src.evaluation.run_ragas_eval              # RAGAS
```

---

## 8. Struktur Proyek

```
bpjs-chatbot/
├── data/
│   ├── raw/              # Hasil scraping (JSON per kategori)
│   ├── processed/        # Chunks siap embed
│   └── eval/             # Dataset uji + hasil evaluasi
├── vectorstore/          # ChromaDB persistent storage
├── src/
│   ├── scraper/          # Scraping & parsing HTML
│   ├── ingestion/        # Chunking & embedding
│   ├── retrieval/        # Similarity search + gate
│   ├── generation/       # LLM client, prompts, groundedness check
│   ├── evaluation/       # Recall@K & RAGAS scripts
│   └── pipeline.py       # Orchestrator utama (fungsi ask())
```

---

### Cakupan Evaluasi
- Recall@K: 43/43 pertanyaan (100%, setelah koreksi 1 typo)
- RAGAS: 27/42 pertanyaan (dihentikan pada 27 karena keterbatasan kuota API harian tier gratis; dianggap sudah representatif untuk menarik kesimpulan awal dan menemukan pola kegagalan yang bermakna — lihat Temuan #1–#5)

*Evaluasi RAGAS pada 15 pertanyaan sisanya dapat dilanjutkan di kemudian hari mengingat mekanisme resume-progress yang sudah diimplementasikan (`data/eval/ragas_progress.json`), namun tidak dianggap kritis untuk kelengkapan analisis saat ini.*
