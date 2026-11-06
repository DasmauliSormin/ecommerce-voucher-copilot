"""Penyimpanan vektor ChromaDB yang persisten dan ingestion idempoten."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

try:
    from .chunker import Chunk
    from .config import CHROMA_DIR, CONSTRAINT_CODES, USE_CONTEXT_HEADER
    from .embedder import Embedder
except (ImportError, ValueError):
    from chunker import Chunk
    from config import CHROMA_DIR, CONSTRAINT_CODES, USE_CONTEXT_HEADER
    from embedder import Embedder

logger = logging.getLogger(__name__)

REQUIRED_METADATA = (
    "doc_id",
    "judul",
    "nomor_dokumen",
    "versi",
    "tanggal_berlaku",
    "departemen",
    "jenis_dokumen",
    "kategori_voucher",
    "kode_batasan_terkait",
    "section_path",
    "chunk_index",
    "total_chunks",
    "jumlah_kata",
    "jumlah_token",
    "terpotong_model",
    "file_sumber",
    "content_hash",
)


def get_client(path: Path | str = CHROMA_DIR) -> chromadb.api.ClientAPI:
    path_obj = Path(path) if isinstance(path, str) else path
    path_obj.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path_obj))


def get_collection(
    client: chromadb.api.ClientAPI,
    name: str,
    extra_metadata: dict[str, Any] | None = None,
):
    meta = {"hnsw:space": "cosine"}
    meta.update(extra_metadata or {})
    return client.get_or_create_collection(
        name=name, metadata=meta, embedding_function=None
    )


def parse_codes(raw: str) -> list[str]:
    parts = [p.strip().upper() for p in raw.replace(";", ",").split(",") if p.strip()]
    unknown = [p for p in parts if p not in CONSTRAINT_CODES]
    if unknown:
        logger.warning("Kode batasan tidak dikenal diabaikan: %s", unknown)
    return [p for p in parts if p in CONSTRAINT_CODES]


def content_hash(embed_text: str) -> str:
    return hashlib.sha1(embed_text.encode("utf-8")).hexdigest()[:12]


def chunk_id(doc_id: str, index: int, digest: str) -> str:
    return f"{doc_id}::{index:04d}::{digest}"


def embedding_text(chunk: Chunk, title: str) -> str:
    if not USE_CONTEXT_HEADER:
        return chunk.text
    return f"{title} | {chunk.section_path}\n{chunk.text}"


@dataclass
class PreparedChunk:
    id: str
    document: str
    embed_text: str
    metadata: dict[str, Any]


def prepare_chunks(
    doc_meta: dict[str, str],
    chunks: list[Chunk],
    token_counts: list[int],
    max_seq_length: int,
) -> list[PreparedChunk]:
    codes = parse_codes(doc_meta.get("kode_batasan_terkait", ""))
    title = doc_meta.get("judul", doc_meta["doc_id"])
    prepared = []
    for chunk, n_tok in zip(chunks, token_counts, strict=True):
        emb_text = embedding_text(chunk, title)
        digest = content_hash(emb_text)
        meta: dict[str, Any] = {
            "doc_id": doc_meta["doc_id"],
            "judul": title,
            "nomor_dokumen": doc_meta.get("nomor_dokumen", ""),
            "versi": doc_meta.get("versi", ""),
            "tanggal_berlaku": doc_meta.get("tanggal_berlaku", ""),
            "departemen": doc_meta.get("departemen", ""),
            "jenis_dokumen": doc_meta.get("jenis_dokumen", ""),
            "kategori_voucher": doc_meta.get("kategori_voucher", "UMUM") or "UMUM",
            "kode_batasan_terkait": ",".join(codes),
            "section_path": chunk.section_path,
            "chunk_index": chunk.chunk_index,
            "total_chunks": len(chunks),
            "jumlah_kata": chunk.word_count,
            "jumlah_token": int(n_tok),
            "terpotong_model": bool(n_tok > max_seq_length),
            "kalimat_dipotong_kata": chunk.has_word_split,
            "file_sumber": doc_meta.get("file_sumber", ""),
            "content_hash": digest,
        }
        for code in CONSTRAINT_CODES:
            meta[f"btsn_{code}"] = code in codes
        prepared.append(
            PreparedChunk(
                id=chunk_id(doc_meta["doc_id"], chunk.chunk_index, digest),
                document=chunk.text,
                embed_text=emb_text,
                metadata=meta,
            )
        )
    return prepared


def _existing_ids(collection, where: dict[str, Any] | None = None) -> set[str]:
    return set(collection.get(where=where, include=[])["ids"])


def upsert_document(
    collection,
    embedder: Embedder,
    doc_id: str,
    prepared: list[PreparedChunk],
    batch_size: int = 256,
) -> dict[str, int]:
    new_ids = {p.id for p in prepared}
    old_ids = _existing_ids(collection, where={"doc_id": doc_id})
    stale = sorted(old_ids - new_ids)
    if stale:
        collection.delete(ids=stale)

    todo = [p for p in prepared if p.id not in old_ids]
    for start in range(0, len(todo), batch_size):
        batch = todo[start : start + batch_size]
        vectors = embedder.embed_passages([p.embed_text for p in batch])
        collection.upsert(
            ids=[p.id for p in batch],
            embeddings=vectors.tolist(),
            documents=[p.document for p in batch],
            metadatas=[p.metadata for p in batch],
        )

    kept = [p for p in prepared if p.id in old_ids]
    for start in range(0, len(kept), batch_size):
        batch = kept[start : start + batch_size]
        collection.update(
            ids=[p.id for p in batch], metadatas=[p.metadata for p in batch]
        )
    return {
        "ditambah": len(todo),
        "dihapus": len(stale),
        "tetap": len(prepared) - len(todo),
    }


def prune_missing_documents(collection, keep_doc_ids: set[str]) -> int:
    data = collection.get(include=["metadatas"])
    orphan = [
        i
        for i, m in zip(data["ids"], data["metadatas"], strict=True)
        if m.get("doc_id") not in keep_doc_ids
    ]
    if orphan:
        collection.delete(ids=orphan)
    return len(orphan)


@dataclass
class IndexReport:
    collection: str
    n_docs: int
    n_chunks: int
    count_after: int
    added: int
    removed: int
    unchanged: int
    token_counts: list[int]
    word_counts: list[int]
    n_truncated: int
    n_word_split: int


def index_corpus(
    docs, embedder: Embedder, size: int, overlap: int, collection
) -> IndexReport:
    try:
        from .chunker import chunk_document
    except (ImportError, ValueError):
        from chunker import chunk_document

    totals = {"ditambah": 0, "dihapus": 0, "tetap": 0}
    tokens: list[int] = []
    words: list[int] = []
    n_word_split = 0
    keep_doc_ids: set[str] = set()

    for doc in docs:
        if isinstance(doc, dict):
            doc_id = (
                doc.get("doc_id")
                or doc.get("id")
                or doc.get("metadata", {}).get("doc_id", "")
            )
            text = (
                doc.get("text")
                or doc.get("content")
                or doc.get("body")
                or doc.get("isi")
                or doc.get("raw_text")
                or ""
            )
            source_file = doc.get("source_file") or doc.get("file_sumber") or ""
            meta_dict = dict(doc.get("meta") or doc.get("metadata") or {})
        else:
            doc_id = getattr(doc, "doc_id", getattr(doc, "id", ""))
            text = getattr(
                doc,
                "text",
                getattr(
                    doc,
                    "content",
                    getattr(doc, "body", getattr(doc, "isi", getattr(doc, "raw_text", ""))),
                ),
            )
            source_file = getattr(
                doc, "source_file", getattr(doc, "file_sumber", "")
            )
            meta_dict = dict(getattr(doc, "meta", getattr(doc, "metadata", {})))

        if not doc_id:
            doc_id = meta_dict.get("doc_id", "DOC_UNKNOWN")

        # Jika teks masih kosong, coba ambil langsung representasi string objek jika ada
        if not text and not isinstance(doc, dict):
            text = str(doc)

        keep_doc_ids.add(doc_id)
        title = meta_dict.get("judul", doc_id)

        chunks = chunk_document(
            text, size, overlap, title=title, allow_plain_headings=True
        )
        if not chunks:
            print(f"[!] Warning: Dokumen '{doc_id}' menghasilkan 0 chunk. Panjang teks: {len(text)}")
            continue

        emb_texts = [embedding_text(c, title) for c in chunks]
        n_tok = embedder.count_tokens(emb_texts, as_passage=True)

        meta_dict.setdefault("doc_id", doc_id)
        meta_dict.setdefault("file_sumber", source_file)

        prepared = prepare_chunks(meta_dict, chunks, n_tok, embedder.max_seq_length)
        stats = upsert_document(collection, embedder, doc_id, prepared)

        for k in totals:
            totals[k] += stats[k]
        tokens.extend(n_tok)
        words.extend(c.word_count for c in chunks)
        n_word_split += sum(c.has_word_split for c in chunks)

    totals["dihapus"] += prune_missing_documents(collection, keep_doc_ids)
    return IndexReport(
        collection=collection.name,
        n_docs=len(docs),
        n_chunks=len(tokens),
        count_after=collection.count(),
        added=totals["ditambah"],
        removed=totals["dihapus"],
        unchanged=totals["tetap"],
        token_counts=tokens,
        word_counts=words,
        n_truncated=sum(t > embedder.max_seq_length for t in tokens),
        n_word_split=n_word_split,
    )