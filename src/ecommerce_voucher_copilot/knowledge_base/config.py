"""Konfigurasi tunggal Knowledge Base Milestone 3.

Semua path, daftar model embedding, konfigurasi chunk, dan parameter retrieval
didefinisikan di sini agar eksperimen dapat direproduksi dan tidak ada nilai
"ajaib" yang tersebar di modul lain.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Path proyek (dihitung relatif terhadap file ini, BUKAN working directory,
# sehingga skrip bisa dijalankan dari folder mana pun).
# config.py -> knowledge_base -> ecommerce_voucher_copilot -> src -> ROOT
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "Data"
CORPUS_DIR = DATA_DIR / "knowledge_base"
CATALOG_PATH = CORPUS_DIR / "catalog.csv"
BENCHMARK_PATH = DATA_DIR / "benchmark" / "queries.json"
CHROMA_DIR = PROJECT_ROOT / "vector_store" / "chroma"
REPORTS_DIR = PROJECT_ROOT / "reports"
THRESHOLDS_PATH = REPORTS_DIR / "thresholds.json"

SUPPORTED_EXTENSIONS = (".md", ".txt", ".pdf")


# ---------------------------------------------------------------------------
# Model embedding yang dibandingkan
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ModelSpec:
    """Spesifikasi satu model Sentence-Transformers."""

    key: str  # nama pendek, dipakai di nama collection (harus singkat)
    hf_name: str  # nama model di Hugging Face Hub
    query_prefix: str = ""  # keluarga E5 wajib "query: "
    passage_prefix: str = ""  # keluarga E5 wajib "passage: "
    note: str = ""


MODELS: dict[str, ModelSpec] = {
    # Baseline: model yang dipakai versi awal. Model ini dilatih untuk
    # Bahasa Inggris dan sengaja dipertahankan sebagai pembanding.
    "enminilm": ModelSpec(
        key="enminilm",
        hf_name="sentence-transformers/all-MiniLM-L6-v2",
        note="baseline Bahasa Inggris",
    ),
    "mminilm": ModelSpec(
        key="mminilm",
        hf_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        note="multilingual, 50+ bahasa termasuk Indonesia",
    ),
    "me5base": ModelSpec(
        key="me5base",
        hf_name="intfloat/multilingual-e5-base",
        query_prefix="query: ",
        passage_prefix="passage: ",
        note="multilingual E5, wajib prefix query/passage",
    ),
    "indoe5": ModelSpec(
        key="indoe5",
        hf_name="LazarusNLP/all-indo-e5-small-v4",
        # Cek kartu model di Hugging Face; jika kartu model tidak memakai
        # prefix, kosongkan dua nilai di bawah dan bangun ulang indeks.
        query_prefix="query: ",
        passage_prefix="passage: ",
        note="E5-small yang di-fine-tune untuk Bahasa Indonesia",
    ),
}


# ---------------------------------------------------------------------------
# Konfigurasi chunking (satuan: KATA, bukan karakter)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ChunkConfig:
    size: int  # jumlah kata maksimum per chunk
    overlap: int  # jumlah kata maksimum yang diulang dari chunk sebelumnya

    @property
    def key(self) -> str:
        return f"{self.size}_{self.overlap}"


CHUNK_CONFIGS: dict[str, ChunkConfig] = {
    c.key: c
    for c in (
        ChunkConfig(128, 25),  # dekat passage 100 kata DPR (Karpukhin dkk., 2020)
        ChunkConfig(200, 40),
        ChunkConfig(320, 60),
    )
}

# Sertakan "judul > section_path" pada teks yang di-embed (bukan teks yang
# ditampilkan). Dapat dimatikan untuk eksperimen ablasi.
USE_CONTEXT_HEADER = True

# ---------------------------------------------------------------------------
# Konfigurasi AKTIF yang dipakai retrieve() di M4.
# PENTING: ubah dua nilai ini SETELAH menjalankan run_benchmark.py, sesuai
# kombinasi dengan metrik terbaik. Jangan dipilih berdasarkan asumsi.
# ---------------------------------------------------------------------------
ACTIVE_MODEL = "me5base"
ACTIVE_CHUNK = "200_40"

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
DEFAULT_TOP_K = 5
CANDIDATE_POOL = 200  # kandidat semantik sebelum fusi hybrid
HYBRID_ALPHA = 0.7  # bobot semantik pada fusi tertimbang (1-alpha untuk BM25)
RRF_K = 60  # konstanta Reciprocal Rank Fusion (Cormack dkk., 2009)

# Dipakai hanya jika reports/thresholds.json belum ada (belum dikalibrasi).
FALLBACK_OOD_THRESHOLD = 0.5

EMBED_BATCH_SIZE = 32
RANDOM_SEED = 16  # untuk split dev/test yang dapat direproduksi

# Kode batasan CSP M2 yang dapat dirujuk dokumen korpus.
CONSTRAINT_CODES = (
    "U1",
    "U2",
    "U3",
    "U4",
    "U5",
    "U6",
    "B1",
    "B2",
    "B3",
    "B4",
    "G1",
    "G2",
    "G3",
)

VOUCHER_CATEGORIES = ("PLATFORM", "CASHBACK", "ONGKIR", "TOKO", "PEMBAYARAN", "UMUM")
DOCUMENT_TYPES = ("SOP", "Kebijakan", "S&K", "Regulasi")


def collection_name(model_key: str, chunk_key: str) -> str:
    """Nama collection ChromaDB untuk satu kombinasi model x konfigurasi chunk.

    ChromaDB mensyaratkan 3-63 karakter alfanumerik/underscore/strip.
    """
    name = f"kb_{model_key}_{chunk_key}"
    if not 3 <= len(name) <= 63:
        raise ValueError(f"Nama collection tidak valid: {name}")
    return name
