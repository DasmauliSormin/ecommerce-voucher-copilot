import os
import sys
import pytest

# Mengarahkan sys.path ke root project dan folder src agar modul selalu terdeteksi
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Menggunakan impor package lengkap yang benar
from cleaner import clean_text


def test_clean_text_normalizing_spaces():
    raw_input = "DOKUMEN    SOP   REGULASI\n\n\nPasal 1  "
    cleaned = clean_text(raw_input)
    assert "DOKUMEN SOP REGULASI" in cleaned
    assert "  " not in cleaned