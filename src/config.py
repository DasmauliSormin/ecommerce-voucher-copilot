import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Data")
CORPUS_RAW_DIR = os.path.join(DATA_DIR, "corpus", "raw")
CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
COLLECTION_NAME = "enterprise_knowledge_base"
SIMILARITY_THRESHOLD = 0.60