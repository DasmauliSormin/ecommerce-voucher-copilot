import chromadb
from config import CHROMA_DB_DIR, COLLECTION_NAME
from embedder import get_embedding_function

def get_vector_store():
    """Menginisialisasi persistent client ChromaDB dan mengembalikan collection."""
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    embedding_ef = get_embedding_function()
    
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection