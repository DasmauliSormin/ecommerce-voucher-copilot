import os
import csv
from typing import List, Dict, Any, Optional

class KnowledgeBaseLoader:
    """Modul untuk membaca dokumen korpus (TXT, MD, PDF) dan metadata catalog."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def load_catalog(self, catalog_path: str) -> Dict[str, Dict[str, Any]]:
        """Membaca file catalog.csv/template.csv untuk pemetaan metadata dokumen."""
        catalog = {}
        if not os.path.exists(catalog_path):
            return catalog

        with open(catalog_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc_id = row.get("doc_id") or row.get("filename")
                if doc_id:
                    catalog[doc_id] = {
                        "title": row.get("title", ""),
                        "category": row.get("category", ""),
                        "source": row.get("filename", "")
                    }
        return catalog

    def load_document(self, file_path: str) -> Dict[str, Any]:
        """Membaca konten teks mentah dari file TXT atau MD."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)

        if ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        else:
            # Fallback membaca file teks generik
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        return {
            "filename": filename,
            "filepath": file_path,
            "content": content,
            "extension": ext
        }

    def load_all_documents(self, corpus_dir: str) -> List[Dict[str, Any]]:
        """Membaca seluruh dokumen yang ada di dalam folder korpus."""
        documents = []
        if not os.path.exists(corpus_dir):
            return documents

        for root, _, files in os.walk(corpus_dir):
            for file in files:
                if file.endswith((".txt", ".md", ".pdf")):
                    full_path = os.path.join(root, file)
                    doc_data = self.load_document(full_path)
                    documents.append(doc_data)
        return documents