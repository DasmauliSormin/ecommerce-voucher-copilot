"""Fungsi pembersihan dan normalisasi teks dokumen."""

from __future__ import annotations

import re

# Fallback import agar aman dijalankan baik via package internal maupun pytest
try:
    from .chunker import Chunk
except (ImportError, ValueError):
    from chunker import Chunk


def clean_text(text: str) -> str:
    """Membersihkan dan menormalisasi teks dokumen.

    - Menghapus karakter kontrol / non-printable.
    - Menormalisasi spasi ganda dan tab menjadi satu spasi.
    - Menjaga struktur baris baru (newline) agar tetap rapi.
    """
    if not text:
        return ""

    # Menghapus karakter kontrol selain newline (\n) dan carriage return (\r)
    text = re.sub(r"[\x00-\x09\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Menormalisasi spasi horizontal (spasi ganda / tab) menjadi satu spasi
    lines = text.splitlines()
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in lines]

    # Menggabungkan kembali dengan menghilangkan baris kosong berturut-turut lebih dari 2
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()