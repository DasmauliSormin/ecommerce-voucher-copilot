import os
import tempfile
import pytest
from ecommerce_voucher_copilot.knowledge_base.cleaner import KnowledgeBaseCleaner
from ecommerce_voucher_copilot.knowledge_base.loader import KnowledgeBaseLoader

def test_cleaner_hyphenation_and_headers():
    dirty_text = "Proses pen-\n jualan dilakukan sesuai aturan. Halaman 1 dari 5\n\n\n\n=== SOP ==="
    cleaned = KnowledgeBaseCleaner.clean_text(dirty_text)
    
    assert "penjualan" in cleaned
    assert "Halaman 1 dari 5" not in cleaned
    assert "===" not in cleaned

def test_loader_read_document():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False, encoding="utf-8") as tmp:
        tmp.write("SOP Voucher Diskon Platform")
        tmp_path = tmp.name

    try:
        loader = KnowledgeBaseLoader(data_dir=os.path.dirname(tmp_path))
        doc = loader.load_document(tmp_path)
        
        assert doc["content"] == "SOP Voucher Diskon Platform"
        assert doc["extension"] == ".txt"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)