import os
import glob
from cleaner import clean_text

def load_raw_corpus(corpus_dir: str) -> list[dict]:
    """Membaca seluruh dokumen SOP dari folder raw."""
    documents = []
    files = glob.glob(os.path.join(corpus_dir, "*.txt"))
    for file_path in sorted(files):
        filename = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
        cleaned_content = clean_text(raw_content)
        documents.append({
            "filename": filename,
            "content": cleaned_content
        })
    return documents