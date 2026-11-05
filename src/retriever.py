from vector_store import get_vector_store
from config import SIMILARITY_THRESHOLD

def retrieve_context(query: str, top_k: int = 3, threshold: float = None):
    """Mengambil dokumen paling relevan menggunakan Cosine Similarity."""
    effective_threshold = threshold if threshold is not None else SIMILARITY_THRESHOLD
    
    collection = get_vector_store()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    if results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        for doc, meta, dist in zip(docs, metas, dists):
            similarity_score = 1.0 - dist
            retrieved.append({
                "document": doc,
                "metadata": meta,
                "cosine_similarity": similarity_score,
                "is_accepted": similarity_score >= effective_threshold
            })
    return retrieved