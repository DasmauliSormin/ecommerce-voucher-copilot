import os
import glob
from config import DATA_DIR, CORPUS_RAW_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from chunker import word_aware_chunking
from vector_store import get_vector_store

def build_vector_index():
    print("=" * 60)
    print("   BUILD INDEX PIPELINE (GRUP 16 - DENSE VECTOR CHROMADB)")
    print("=" * 60)
    
    target_dir = os.path.join(DATA_DIR, "knowledge_base")
    if not os.path.exists(target_dir):
        target_dir = CORPUS_RAW_DIR

    txt_files = glob.glob(os.path.join(target_dir, "*.txt"))
    if not txt_files:
        print(f"[!] Tidak ada file .txt ditemukan di {target_dir}")
        return

    collection = get_vector_store()
    
    documents = []
    metadatas = []
    ids = []
    total_chunks = 0

    for file_path in sorted(txt_files):
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = word_aware_chunking(content, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{filename}_chunk_{idx}"
            documents.append(chunk)
            metadatas.append({
                "source": filename,
                "chunk_index": idx,
                "total_chunks": len(chunks)
            })
            ids.append(chunk_id)
            total_chunks += 1

    # Menggunakan upsert untuk menjamin sifat Idempotensi
    collection.upsert(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[+] Berhasil mengindeks {len(txt_files)} file dokumen.")
    print(f"[+] Total chunk tersimpan: {total_chunks}")
    print(f"[+] Idempotensi teruji! Total record di ChromaDB: {collection.count()}")
    print("=" * 60)

if __name__ == "__main__":
    build_vector_index()