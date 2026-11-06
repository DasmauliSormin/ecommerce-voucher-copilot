# Milestone 3 — Knowledge Base Kebijakan Promo & Vector Semantic Search

## Struktur
```
src/ecommerce_voucher_copilot/knowledge_base/
  config.py        # SATU-SATUNYA tempat konfigurasi (path, model, chunk, threshold)
  loader.py        # baca .md/.txt/.pdf + catalog.csv
  cleaner.py       # normalisasi unicode, header/footer & nomor halaman PDF, hyphenation
  chunker.py       # recursive word-aware chunking: heading > paragraf > kalimat > kata
  embedder.py      # Sentence-Transformers (normalisasi L2, prefix E5, hitung token)
  vector_store.py  # ChromaDB persisten (cosine), metadata lengkap, upsert idempoten
  retriever.py     # semantik / BM25 / hybrid + filter where & where_document + OOD
  benchmark.py     # Hit@k, Precision@k, Recall@k, MRR, nDCG@5, kalibrasi threshold OOD
src/build_index.py     # CLI bangun indeks semua model x konfigurasi chunk
src/search_kb.py       # CLI pencarian (filter kategori/departemen/batasan/kata kunci)
src/run_benchmark.py   # CLI benchmark -> reports/*.csv, *.png, thresholds.json
Data/knowledge_base/   # korpus + catalog.csv
Data/benchmark/queries.json
```

## Menjalankan
```
uv sync
uv run python src/build_index.py            # membangun 4 model x 3 konfigurasi = 12 collection
uv run python src/run_benchmark.py          # hasil di reports/
uv run python src/search_kb.py "kenapa voucher ongkir tidak bisa dipakai bersama diskon toko?"
uv run pytest -q
uv run ruff format src tests
```
Setelah benchmark, set `ACTIVE_MODEL` dan `ACTIVE_CHUNK` di `config.py` sesuai `reports/best_config.json`.

## Antarmuka untuk M4
```python
from ecommerce_voucher_copilot.knowledge_base import retrieve
hasil = retrieve("kenapa cashback GOPAY saya tidak masuk?", k=5, filters={"kategori_voucher": "CASHBACK"})
if hasil.is_out_of_domain:
    ...  # agen menolak menjawab dari korpus
for c in hasil.chunks:
    print(c.cosine_similarity, c.citation, c.document)
```
