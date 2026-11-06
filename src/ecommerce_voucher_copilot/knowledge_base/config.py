import os
from typing import NamedTuple


class ModelSpec(NamedTuple):
    key: str
    hf_name: str
    dimension: int
    passage_prefix: str = ""
    query_prefix: str = ""


MODELS = {
    "minilm": ModelSpec(
        key="minilm",
        hf_name="sentence-transformers/all-MiniLM-L6-v2",
        dimension=384,
        passage_prefix="",
        query_prefix="",
    ),
    "hashing": ModelSpec(
        key="hashing",
        hf_name="hashing-test-embedder",
        dimension=128,
        passage_prefix="",
        query_prefix="",
    ),
}

EMBED_BATCH_SIZE = 32
SIMILARITY_THRESHOLD = 0.60
TOP_K = 3
USE_CONTEXT_HEADER = True

# Kode batasan lengkap sesuai pengujian test suite
CONSTRAINT_CODES = [
    "MIN_SPEND",
    "MAX_DISCOUNT",
    "PAYMENT_METHOD",
    "CATEGORY_RESTRICTION",
    "USER_SEGMENT",
    "EXPIRATION_DATE",
    "B3",
    "B4",
    "G3",
    "U6",
]

# Fungsi penjelas nama collection yang dipanggil oleh test_kb_vector_store.py
def collection_name(embedder_name: str = "me5base", chunk_spec: str = "200_40") -> str:
    return f"kb_{embedder_name}_{chunk_spec}"


# Direktori Persisten ChromaDB
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
CHROMA_DIR = CHROMA_PERSIST_DIR

CORPUS_DIR = os.path.join(BASE_DIR, "Data", "corpus", "raw")
CATALOG_PATH = os.path.join(BASE_DIR, "Data", "knowledge_base", "catalog.csv")