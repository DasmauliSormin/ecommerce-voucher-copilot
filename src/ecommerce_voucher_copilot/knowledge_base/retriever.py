import os
import sys
from typing import Any, Dict, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
  sys.path.insert(0, CURRENT_DIR)

try:
  from .vector_store import get_client, get_collection
  from .embedder import HashingEmbedder, get_embedder
  from . import config
except (ImportError, ValueError):
  from vector_store import get_client, get_collection
  from embedder import HashingEmbedder, get_embedder
  import config

CHROMA_DIR = getattr(config, "CHROMA_DIR", None)
COLLECTION_NAME = getattr(
    config, "COLLECTION_NAME", getattr(config, "CHROMA_COLLECTION_NAME", "vouchers")
)
SIMILARITY_THRESHOLD = getattr(config, "SIMILARITY_THRESHOLD", 0.35)
DEFAULT_MODEL_KEY = getattr(config, "DEFAULT_MODEL_KEY", "minilm")


class KnowledgeBaseRetriever:

  def __init__(self, embedder_key: str = DEFAULT_MODEL_KEY):
    self.client = get_client(CHROMA_DIR)
    self.collection = get_collection(self.client, COLLECTION_NAME)
    try:
      self.embedder = get_embedder(embedder_key)
    except Exception:
      self.embedder = HashingEmbedder()

  def retrieve(self, query: str, top_k: int = 1) -> List[Dict[str, Any]]:
    query_vector = self.embedder.embed_queries([query])[0]

    if self.collection.count() == 0:
      return [{
          "document": "",
          "metadata": {},
          "cosine_similarity": 0.0,
          "is_accepted": False,
      }]

    res = self.collection.query(
        query_embeddings=[query_vector.tolist()],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    results = []
    if res and res.get("distances") and res["distances"][0]:
      for i in range(len(res["distances"][0])):
        dist = res["distances"][0][i]
        sim_score = 1.0 - dist
        doc = res["documents"][0][i] if res.get("documents") else ""
        meta = res["metadatas"][0][i] if res.get("metadatas") else {}

        results.append({
            "document": doc,
            "metadata": meta,
            "cosine_similarity": sim_score,
            "is_accepted": sim_score >= SIMILARITY_THRESHOLD,
        })

    if not results:
      results.append({
          "document": "",
          "metadata": {},
          "cosine_similarity": 0.0,
          "is_accepted": False,
      })

    return results


_retriever_instance = None


def retrieve_context(query: str, top_k: int = 1) -> List[Dict[str, Any]]:
  global _retriever_instance
  if _retriever_instance is None:
    _retriever_instance = KnowledgeBaseRetriever()
  return _retriever_instance.retrieve(query, top_k=top_k)