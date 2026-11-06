import os
import sys
import pytest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

KB_DIR = os.path.join(
    PROJECT_ROOT, "src", "ecommerce_voucher_copilot", "knowledge_base"
)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if KB_DIR not in sys.path:
  sys.path.insert(0, KB_DIR)
if SRC_DIR not in sys.path:
  sys.path.insert(0, SRC_DIR)

try:
  from embedder import HashingEmbedder
  from vector_store import get_client, get_collection, index_corpus
except ImportError:
  from ecommerce_voucher_copilot.knowledge_base.embedder import HashingEmbedder
  from ecommerce_voucher_copilot.knowledge_base.vector_store import (
      get_client,
      get_collection,
      index_corpus,
  )


class MockDoc:

  def __init__(
      self,
      doc_id: str,
      text: str,
      source_file: str = "test.txt",
      meta: dict = None,
  ):
    self.doc_id = doc_id
    self.text = text
    self.source_file = source_file
    default_meta = {
        "doc_id": doc_id,
        "judul": doc_id,
        "nomor_dokumen": doc_id,
        "versi": "1.0",
        "tanggal_berlaku": "2026-01-01",
        "departemen": "Marketing",
        "jenis_dokumen": "SOP",
        "kategori_voucher": "DISCOUNT",
        "kode_batasan_terkait": "B3,B4,G3" if doc_id == "KB01" else "B3",
        "file_sumber": source_file,
    }
    if meta:
      default_meta.update(meta)
    self.meta = default_meta


@pytest.fixture
def embedder():
  return HashingEmbedder()


@pytest.fixture
def indexed(tmp_path, embedder):
  client = get_client(tmp_path / "chroma")
  col = get_collection(client, "kb_test_40_10")
  docs = [
      MockDoc(
          "KB01",
          "# Syarat Voucher Diskon\n\n## 3.2 Aturan Stacking\n\nIni adalah"
          " syarat penggunaan voucher diskon belanja minimal 100 ribu rupiah.",
      ),
      MockDoc(
          "KB06",
          "# Ketentuan Ketat\n\nNominal maksimal voucher adalah Rp1.000.000"
          " untuk pembelian produk elektronik.",
      ),
  ]
  report = index_corpus(docs, embedder, size=200, overlap=20, collection=col)

  data = col.get(include=["metadatas"])
  for i, m in zip(data["ids"], data["metadatas"], strict=True):
    if m.get("doc_id") == "KB01":
      m["section_path"] = "Syarat Voucher Diskon > 3.2 Aturan Stacking"
      col.update(ids=[i], metadatas=[m])

  return {
      "client": client,
      "collection": col,
      "docs": docs,
      "report": report,
  }