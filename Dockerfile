FROM python:3.11-slim

# Install system dependencies yang dibutuhkan lxml (libxml2, libxslt)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dulu (supaya Docker cache layer ini, build lebih cepat kalau cuma kode yang berubah)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua kode project
COPY . .

# Jalankan startup.py dulu (cek/isi data), baru start server
CMD python startup.py && uvicorn api.main:app --host 0.0.0.0 --port $PORT