"""CLI: bangun indeks ChromaDB untuk setiap kombinasi model x konfigurasi chunk.

Contoh:
    uv run python src/build_index.py                       # semua model & konfigurasi
    uv run python src/build_index.py --models me5base --configs 200_40
    uv run python src/build_index.py --reset               # hapus collection lalu bangun ulang
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent)
)  # agar paket di src/ dapat diimpor

from ecommerce_voucher_copilot.knowledge_base.cleaner import clean_text  # noqa: E402
from ecommerce_voucher_copilot.knowledge_base.config import (  # noqa: E402
    CHUNK_CONFIGS,
    DATA_DIR,
    MODELS,
    REPORTS_DIR,
    collection_name,
)
from ecommerce_voucher_copilot.knowledge_base.embedder import (
    count_parameters,
    get_embedder,
)  # noqa: E402
from ecommerce_voucher_copilot.knowledge_base.loader import load_corpus  # noqa: E402
from ecommerce_voucher_copilot.knowledge_base.vector_store import (
    get_client,
    get_collection,
    index_corpus,
)  # noqa: E402

CLEAN_DIR = DATA_DIR / "cleaned"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bangun indeks vektor Knowledge Base BelanjaHemat"
    )
    p.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    p.add_argument(
        "--configs", nargs="+", default=list(CHUNK_CONFIGS), choices=list(CHUNK_CONFIGS)
    )
    p.add_argument(
        "--reset",
        action="store_true",
        help="hapus collection terkait sebelum membangun",
    )
    return p.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="[%(levelname)s] %(message)s")
    args = parse_args()

    print("=" * 78)
    print("BUILD INDEX - KNOWLEDGE BASE KEBIJAKAN PROMO BELANJAHEMAT (KELOMPOK 16)")
    print("=" * 78)

    try:
        docs = load_corpus()
    except (FileNotFoundError, ValueError) as exc:
        print(f"[GAGAL] {exc}")
        return 1

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    for d in docs:
        d.text = clean_text(d.text, is_pdf=d.is_pdf)
        (CLEAN_DIR / f"{d.doc_id}.md").write_text(d.text, encoding="utf-8")
    n_pdf = sum(d.is_pdf for d in docs)
    print(
        f"[+] {len(docs)} dokumen dimuat ({n_pdf} PDF), teks bersih disimpan di {CLEAN_DIR}"
    )

    client = get_client()
    rows = []
    all_ok = True
    for model_key in args.models:
        try:
            t0 = time.perf_counter()
            embedder = get_embedder(model_key)
            load_s = time.perf_counter() - t0
        except Exception as exc:  # model gagal diunduh/dimuat: lanjut ke model lain
            print(f"[LEWATI] Model {model_key}: {exc}")
            all_ok = False
            continue
        print(
            f"\n[MODEL] {embedder.name} | dimensi={embedder.dimension} | max_seq_length={embedder.max_seq_length}"
        )

        for chunk_key in args.configs:
            cfg = CHUNK_CONFIGS[chunk_key]
            name = collection_name(model_key, chunk_key)
            if args.reset:
                try:
                    client.delete_collection(name)
                except Exception:  # collection belum ada
                    pass
            col = get_collection(
                client,
                name,
                {
                    "model": embedder.name,
                    "chunk_size": cfg.size,
                    "chunk_overlap": cfg.overlap,
                },
            )

            t0 = time.perf_counter()
            r1 = index_corpus(docs, embedder, cfg.size, cfg.overlap, col)
            build_s = time.perf_counter() - t0
            # Uji idempotensi: jalankan ingestion kedua kali; tidak boleh ada perubahan.
            r2 = index_corpus(docs, embedder, cfg.size, cfg.overlap, col)
            idempotent = (
                r1.count_after == r2.count_after == r1.n_chunks
                and r2.added == 0
                and r2.removed == 0
            )
            all_ok &= idempotent

            pct_trunc = 100 * r1.n_truncated / max(r1.n_chunks, 1)
            print(
                f"  {name:<28} chunk={r1.n_chunks:<4} count={r2.count_after:<4} "
                f"ditambah={r1.added:<4} dihapus={r1.removed:<3} terpotong={pct_trunc:5.1f}% "
                f"waktu={build_s:6.1f}s idempoten={'YA' if idempotent else 'TIDAK'}"
            )
            rows.append(
                {
                    "collection": name,
                    "model": embedder.name,
                    "dimensi": embedder.dimension,
                    "max_seq_length": embedder.max_seq_length,
                    "parameter": count_parameters(embedder),
                    "waktu_muat_model_s": round(load_s, 2),
                    "chunk_size": cfg.size,
                    "chunk_overlap": cfg.overlap,
                    "n_dokumen": r1.n_docs,
                    "n_chunk": r1.n_chunks,
                    "count_run1": r1.count_after,
                    "count_run2": r2.count_after,
                    "ditambah_run2": r2.added,
                    "dihapus_run2": r2.removed,
                    "idempoten": idempotent,
                    "pct_terpotong_model": round(pct_trunc, 2),
                    "n_kalimat_dipotong_kata": r1.n_word_split,
                    "waktu_build_s": round(build_s, 2),
                }
            )

    if rows:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        out = REPORTS_DIR / "index_report.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n[+] Ringkasan indeks disimpan: {out}")
    print("=" * 78)
    print(
        "STATUS:",
        "SEMUA BERHASIL & IDEMPOTEN"
        if all_ok and rows
        else "ADA YANG GAGAL - periksa log di atas",
    )
    return 0 if all_ok and rows else 1


if __name__ == "__main__":
    sys.exit(main())
