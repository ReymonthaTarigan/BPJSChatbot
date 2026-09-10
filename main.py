"""
main.py (di root project)
File ini cuma sebagai jembatan supaya FastAPI Cloud (yang secara default
mencari main.py di root) bisa menemukan aplikasi kita yang sebenarnya
berada di api/main.py
"""

from api.main import app