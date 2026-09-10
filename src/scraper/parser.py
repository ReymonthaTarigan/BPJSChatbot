"""
parser.py
Parsing HTML BPJS berbasis struktur accordion FAQ (Bootstrap).

Struktur HTML:
- Tiap panduan = 1 <li data-aos="fade-up"> di level atas
- Judul panduan = teks di dalam <a data-bs-toggle="collapse">
- Konten (deskripsi + langkah) = di dalam <div class="collapse">
  - Deskripsi = teks <p> TIDAK TERMASUK <ol> yang nested di dalamnya
  - Langkah = semua <li> di dalam <ol> yang nested di dalam <p> tsb
"""
import re
from bs4 import BeautifulSoup
from typing import List, Dict


def clean_text(text: str) -> str:
    """
    Gabungkan hasil get_text() dengan separator spasi, lalu normalize
    spasi berlebih (termasuk newline/tab) jadi 1 spasi saja.
    """
    return re.sub(r'\s+', ' ', text).strip()


def parse_panduan_page(html: str, source_url: str, kategori: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    panduan_list = []

    faq_section = soup.find("section", id="faq")
    if not faq_section:
        return panduan_list

    faq_items = faq_section.select("li[data-aos='fade-up']")

    for item in faq_items:
        link_tag = item.find("a", attrs={"data-bs-toggle": "collapse"})
        if not link_tag:
            continue
        judul = clean_text(link_tag.get_text(separator=" "))

        content_div = item.find("div", class_="collapse")
        if not content_div:
            continue

        p_tag = content_div.find("p")
        deskripsi = clean_text(p_tag.get_text(separator=" ")) if p_tag else ""

        ol_tag = content_div.find("ol")
        langkah = []
        if ol_tag:
            langkah = [clean_text(li.get_text(separator=" ")) for li in ol_tag.find_all("li")]
        elif deskripsi:
                    # Kasus tidak ada <ol>, tapi ada teks di <p>.
                    # Anggap seluruh isi <p> sebagai "langkah tunggal",
                    # supaya panduan singkat seperti ini tetap tertangkap,
                    # tidak di-skip begitu saja.
                    langkah = [deskripsi]
                    deskripsi = ""
        if not langkah:
            continue

        panduan_list.append({
            "kategori": kategori,
            "judul": judul,
            "deskripsi": deskripsi,
            "langkah": langkah,
            "sumber_url": source_url
        })

    return panduan_list