import os
import sys
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "..", "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from chunker import word_aware_chunking
from vector_store import get_vector_store

def test_word_aware_chunking():
    """Uji pemotongan teks terstruktur tanpa memotong kata."""
    text = "SOP Regulasi Penggunaan Voucher Diskon E-Commerce Enterprise Platform"
    chunks = word_aware_chunking(text, chunk_size=30, overlap=5)
    
    assert len(chunks) > 0
    assert isinstance(chunks, list)
    for chunk in chunks:
        assert len(chunk) <= 35


def test_chromadb_idempotency():
    """Uji Idempotensi: Upsert data sama 2 kali tidak menyebabkan duplikasi di ChromaDB."""
    collection = get_vector_store()
    
    test_id = "test_doc_idempotent_01"
    collection.upsert(
        documents=["Teks uji idempotensi data ChromaDB."],
        metadatas=[{"source": "test.txt"}],
        ids=[test_id]
    )
    
    count_after_first = collection.count()
    
    collection.upsert(
        documents=["Teks uji idempotensi data ChromaDB."],
        metadatas=[{"source": "test.txt"}],
        ids=[test_id]
    )
    
    count_after_second = collection.count()
    assert count_after_first == count_after_second