import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from retriever import retrieve_context

def test_ood_rejection_threshold():
    query = "Bagaimana resep membuat kue bolu pandan yang empuk?"
    results = retrieve_context(query, top_k=1)
    assert len(results) > 0
    assert results[0]["is_accepted"] is False
    assert results[0]["cosine_similarity"] < 0.60