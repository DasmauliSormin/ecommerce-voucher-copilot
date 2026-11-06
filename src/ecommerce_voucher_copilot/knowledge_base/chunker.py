"""Word-aware recursive chunking yang menghormati struktur dokumen.

Hierarki pemisah: heading -> paragraf/butir -> kalimat -> kata.
- Chunk TIDAK PERNAH melintasi batas section, sehingga setiap chunk memiliki
  satu section_path yang jelas (misal "Bab 3 Ketentuan > 3.2 Aturan Stacking").
- Chunk disusun dari kalimat utuh. Pemotongan di level kata hanya terjadi bila
  SATU kalimat lebih panjang dari chunk_size; kasus ini ditandai
  (has_word_split=True) dan dilaporkan di statistik.
- Overlap diambil dari kalimat utuh di ekor chunk sebelumnya dengan total
  kata <= overlap (overlap tidak memotong kalimat).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MD_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_BAB_HEADING = re.compile(r"^(BAB\s+[IVXLC\d]+\b.*)$", re.IGNORECASE)
_NUM_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{0,78})$")
_LIST_ITEM = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]|[a-z][.)]|[-*])\s+", re.IGNORECASE)

# Singkatan yang diakhiri titik tetapi BUKAN akhir kalimat.
_ABBREVIATIONS = {
    "no",
    "nomor",
    "dll",
    "dsb",
    "dst",
    "tsb",
    "yth",
    "sbb",
    "hlm",
    "hal",
    "psl",
    "ps",
    "kab",
    "jl",
    "tgl",
    "bpk",
    "ibu",
    "sdr",
    "dr",
    "drs",
    "ir",
    "prof",
    "pt",
    "tbk",
    "cv",
    "a.n",
    "u.p",
    "s.d",
    "vs",
    "min",
    "maks",
    "max",
    "rp",
    "ttd",
    "kep",
    "per",
    "sk",
    "uu",
    "pp",
    "permendag",
    "jo",
    "bab",
}
# Kandidat batas kalimat: tanda baca akhir + spasi + awal kalimat baru.
_SENT_BOUNDARY = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9])")


_CONNECTORS = {
    "dan",
    "atau",
    "di",
    "ke",
    "dari",
    "untuk",
    "pada",
    "dengan",
    "yang",
    "serta",
    "&",
    "-",
    "/",
}


def is_title_like(text: str) -> bool:
    """Judul cenderung Title Case: 'Aturan Stacking', 'Batas Transaksi COD'.

    Membedakan heading bernomor ('3.2 Aturan Stacking') dari butir daftar
    bernomor ('1. Voucher platform tidak dapat digabung').
    """
    words = [
        w for w in re.findall(r"[A-Za-z][\w&/-]*", text) if w.lower() not in _CONNECTORS
    ]
    if not words:
        return False
    capital = sum(w[0].isupper() for w in words)
    return capital / len(words) >= 0.6


@dataclass
class Section:
    path: tuple[str, ...]
    text: str


@dataclass
class Chunk:
    text: str
    section_path: str
    chunk_index: int
    word_count: int
    sentence_count: int
    has_word_split: bool = False


def _heading_level(line: str, allow_plain: bool) -> tuple[int, str] | None:
    m = _MD_HEADING.match(line)
    if m:
        return len(m.group(1)), m.group(2).strip()
    if not allow_plain:
        return None
    m = _BAB_HEADING.match(line)
    if m:
        return 1, m.group(1).strip()
    m = _NUM_HEADING.match(line)
    if (
        m
        and not line.rstrip().endswith((".", ":", ";", ","))
        and is_title_like(m.group(2))
    ):
        return 1 + m.group(1).count("."), line.strip()
    return None


def split_sections(
    text: str, title: str = "", allow_plain_headings: bool = True
) -> list[Section]:
    """Memecah dokumen menjadi section berdasarkan heading.

    Heading markdown (#) selalu dikenali. Heading teks polos ("BAB 3 ...",
    "3.2 Aturan Stacking") dikenali bila allow_plain_headings=True, berguna
    untuk teks hasil ekstraksi PDF yang kehilangan tanda '#'.
    """
    stack: list[tuple[int, str]] = []
    sections: list[Section] = []
    buffer: list[str] = []

    def flush() -> None:
        body = "\n".join(buffer).strip()
        if body:
            path = tuple(h for _, h in stack) or (
                (title,) if title else ("(tanpa judul)",)
            )
            sections.append(Section(path=path, text=body))
        buffer.clear()

    for line in text.split("\n"):
        head = _heading_level(line.strip(), allow_plain_headings)
        if head:
            flush()
            level, name = head
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, name))
        else:
            buffer.append(line)
    flush()

    # Heading level-1 yang sama dengan judul dokumen tidak perlu diulang di path.
    if title:
        for s in sections:
            if len(s.path) > 1 and s.path[0].casefold() == title.casefold():
                s.path = s.path[1:]
    return sections


def _paragraph_units(section_text: str) -> list[str]:
    """Paragraf dan butir daftar menjadi unit tersendiri; baris lanjutan digabung."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", section_text):
        current = ""
        for line in para.split("\n"):
            s = line.strip()
            if not s:
                continue
            if _LIST_ITEM.match(s) or s.startswith("|") or not current:
                if current:
                    units.append(current)
                current = s
            else:
                current = f"{current} {s}"
        if current:
            units.append(current)
    return units


def split_sentences(text: str) -> list[str]:
    """Pemecah kalimat Bahasa Indonesia dengan perlindungan singkatan dan angka.

    Tidak memecah pada "Rp50.000", "3.2", "No. 12", "dll.", atau penanda butir
    "a." / "1." di awal teks.
    """
    text = text.strip()
    if not text:
        return []
    pieces: list[str] = []
    start = 0
    for m in _SENT_BOUNDARY.finditer(text):
        candidate = text[start : m.start()].strip()
        last_token = re.split(r"\s+", candidate)[-1] if candidate else ""
        bare = last_token.rstrip(".\"')]").lower()
        is_abbrev = bare in _ABBREVIATIONS or bool(re.fullmatch(r"[a-z]", bare))
        is_marker = (
            bool(re.fullmatch(r"\d+(?:\.\d+)*\.?", last_token))
            and len(candidate.split()) == 1
        )
        if is_abbrev or is_marker:
            continue
        pieces.append(candidate)
        start = m.end()
    tail = text[start:].strip()
    if tail:
        pieces.append(tail)
    return pieces


def _words(s: str) -> int:
    return len(s.split())


def _split_long_sentence(sentence: str, size: int) -> list[str]:
    words = sentence.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def chunk_section(
    sentences: list[str], size: int, overlap: int
) -> list[tuple[str, int, bool]]:
    """Kemas kalimat menjadi chunk. Mengembalikan (teks, jumlah_kalimat, word_split)."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Syarat: size > 0 dan 0 <= overlap < size")

    units: list[tuple[str, bool]] = []
    for sent in sentences:
        if _words(sent) > size:
            units.extend((part, True) for part in _split_long_sentence(sent, size))
        else:
            units.append((sent, False))

    chunks: list[tuple[str, int, bool]] = []
    current: list[tuple[str, bool]] = []
    n_new = 0  # jumlah unit baru (bukan overlap) di chunk berjalan

    def emit() -> None:
        chunks.append(
            (" ".join(u for u, _ in current), len(current), any(w for _, w in current))
        )

    for unit in units:
        if current and _words(" ".join(u for u, _ in current)) + _words(unit[0]) > size:
            emit()
            tail: list[tuple[str, bool]] = []
            budget = overlap
            for prev in reversed(current):
                if prev[1] or _words(prev[0]) > budget:
                    break
                tail.insert(0, prev)
                budget -= _words(prev[0])
            # Overlap + unit baru tidak boleh melebihi size.
            while (
                tail and _words(" ".join(u for u, _ in tail)) + _words(unit[0]) > size
            ):
                tail.pop(0)
            current = tail
            n_new = 0
        current.append(unit)
        n_new += 1
    if current and n_new:
        emit()
    return chunks


def chunk_document(
    text: str,
    size: int,
    overlap: int,
    title: str = "",
    allow_plain_headings: bool = True,
) -> list[Chunk]:
    """Chunk seluruh dokumen. chunk_index berurutan dalam satu dokumen."""
    result: list[Chunk] = []
    for section in split_sections(
        text, title=title, allow_plain_headings=allow_plain_headings
    ):
        sentences: list[str] = []
        for unit in _paragraph_units(section.text):
            sentences.extend(split_sentences(unit))
        for body, n_sent, word_split in chunk_section(sentences, size, overlap):
            result.append(
                Chunk(
                    text=body,
                    section_path=" > ".join(section.path),
                    chunk_index=len(result),
                    word_count=_words(body),
                    sentence_count=n_sent,
                    has_word_split=word_split,
                )
            )
    return result
