import os
import sys
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
KB_DIR = os.path.join(PROJECT_ROOT, "src", "ecommerce_voucher_copilot", "knowledge_base")

if KB_DIR not in sys.path:
    sys.path.insert(0, KB_DIR)

from retriever import retrieve_context


def test_ood_rejection_threshold():
    """Kueri di luar domain harus menghasilkan nilai similarity < 0.35 dan ditolak."""
    query = "Bagaimana resep membuat kue bolu pandan yang empuk?"
    results = retrieve_context(query, top_k=1)
    assert len(results) > 0
    assert results[0]["is_accepted"] is False
    assert results[0]["cosine_similarity"] < 0.35