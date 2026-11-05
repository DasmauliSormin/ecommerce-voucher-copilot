import os
import sys
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from cleaner import clean_text

def test_clean_text_normalizing_spaces():
    raw_input = "DOKUMEN    SOP   REGULASI\n\n\nPasal 1  "
    cleaned = clean_text(raw_input)
    assert "DOKUMEN SOP REGULASI" in cleaned
    assert "  " not in cleaned