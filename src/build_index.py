import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
KB_DIR = os.path.join(CURRENT_DIR, "ecommerce_voucher_copilot", "knowledge_base")

for p in [CURRENT_DIR, KB_DIR, PROJECT_ROOT]:
  if p not in sys.path:
    sys.path.insert(0, p)

try:
  from loader import load_corpus
  from embedder import get_embedder
  from vector_store import get_client, get_collection, index_corpus
  import config
except ImportError:
  from ecommerce_voucher_copilot.knowledge_base.loader import load_corpus
  from ecommerce_voucher_copilot.knowledge_base.embedder import get_embedder
  from ecommerce_voucher_copilot.knowledge_base.vector_store import (
      get_client,
      get_collection,
      index_corpus,
  )
  from ecommerce_voucher_copilot.knowledge_base import config


def main():
  print("=" * 70)
  print("   MEMBANGUN INDEX CHROMADB (INGESTION KORPUS DOKUMEN)")
  print("=" * 70)

  corpus_dir = os.path.join(PROJECT_ROOT, "Data", "corpus")
  if not os.path.exists(corpus_dir):
    corpus_dir = os.path.join(PROJECT_ROOT, "Data")

  print(f"[+] Memuat korpus dari: {corpus_dir}")
  docs = load_corpus(corpus_dir)
  print(f"[+] Berhasil memuat {len(docs)} dokumen.")

  embedder_key = getattr(config, "DEFAULT_MODEL_KEY", "minilm")
  embedder = get_embedder(embedder_key)
  client = get_client(getattr(config, "CHROMA_DIR", None))
  col = get_collection(client, getattr(config, "COLLECTION_NAME", "vouchers"))

  report = index_corpus(docs, embedder, size=200, overlap=20, collection=col)
  print("[+] Ingestion Selesai!")
  print(f"    - Total Dokumen: {report.n_docs}")
  print(f"    - Total Chunk: {report.n_chunks}")
  print(
      f"    - Ditambah: {report.added}, Dihapus: {report.removed}, Tetap:"
      f" {report.unchanged}"
  )
  print(f"    - Jumlah Chunk di Database: {report.count_after}")
  print("=" * 70)


if __name__ == "__main__":
  main()