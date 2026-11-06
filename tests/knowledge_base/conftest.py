"""Fixture bersama untuk test Knowledge Base (offline, tanpa unduh model)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from _kb_samples import CATALOG, DOC_COD, DOC_STACKING  # noqa: E402

from ecommerce_voucher_copilot.knowledge_base.embedder import HashingEmbedder  # noqa: E402


@pytest.fixture
def corpus_dir(tmp_path: Path) -> Path:
    d = tmp_path / "knowledge_base"
    d.mkdir()
    (d / "kb01_stacking.md").write_text(DOC_STACKING, encoding="utf-8")
    (d / "kb06_pembayaran.txt").write_text(DOC_COD, encoding="utf-8")
    (d / "catalog.csv").write_text(CATALOG, encoding="utf-8")
    return d


@pytest.fixture
def embedder() -> HashingEmbedder:
    return HashingEmbedder()


@pytest.fixture
def chroma_client(tmp_path: Path):
    from ecommerce_voucher_copilot.knowledge_base.vector_store import get_client

    return get_client(tmp_path / "chroma")


@pytest.fixture
def indexed(corpus_dir, embedder, chroma_client):
    """Collection yang sudah diindeks dari korpus contoh."""
    from ecommerce_voucher_copilot.knowledge_base.cleaner import clean_text
    from ecommerce_voucher_copilot.knowledge_base.loader import load_corpus
    from ecommerce_voucher_copilot.knowledge_base.vector_store import (
        get_collection,
        index_corpus,
    )

    docs = load_corpus(corpus_dir, corpus_dir / "catalog.csv")
    for d in docs:
        d.text = clean_text(d.text, is_pdf=d.is_pdf)
    col = get_collection(chroma_client, "kb_test_40_10")
    report = index_corpus(docs, embedder, 40, 10, col)
    return {"docs": docs, "collection": col, "report": report}
