"""Test ChromaDB: persistensi, idempotensi, metadata lengkap, ID deterministik."""

from __future__ import annotations

from ecommerce_voucher_copilot.knowledge_base.config import (
    CONSTRAINT_CODES,
    collection_name,
)
from ecommerce_voucher_copilot.knowledge_base.vector_store import (
    REQUIRED_METADATA,
    get_client,
    get_collection,
    index_corpus,
    parse_codes,
)


def test_ingestion_idempoten_saat_dijalankan_dua_kali(indexed, embedder):
    col, docs, r1 = indexed["collection"], indexed["docs"], indexed["report"]
    assert r1.count_after == r1.n_chunks > 0
    r2 = index_corpus(docs, embedder, 40, 10, col)
    assert r2.count_after == r1.count_after
    assert (r2.added, r2.removed, r2.unchanged) == (0, 0, r1.n_chunks)


def test_revisi_dokumen_menghapus_chunk_usang(indexed, embedder):
    col, docs = indexed["collection"], indexed["docs"]
    before = set(col.get(where={"doc_id": "KB06"}, include=[])["ids"])
    docs[1].text = docs[1].text.replace("Rp1.000.000", "Rp1.500.000")
    r = index_corpus(docs, embedder, 40, 10, col)
    after = set(col.get(where={"doc_id": "KB06"}, include=[])["ids"])
    assert r.removed >= 1 and before != after
    assert col.count() == r.n_chunks  # tidak ada sisa chunk lama


def test_dokumen_yang_dihapus_dari_korpus_ikut_dihapus(indexed, embedder):
    col, docs = indexed["collection"], indexed["docs"]
    r = index_corpus(docs[:1], embedder, 40, 10, col)  # KB06 dikeluarkan dari korpus
    doc_ids = {meta["doc_id"] for meta in col.get(include=["metadatas"])["metadatas"]}
    assert doc_ids == {"KB01"}
    assert col.count() == r.n_chunks


def test_metadata_lengkap_dan_tipe_valid(indexed):
    metas = indexed["collection"].get(include=["metadatas"])["metadatas"]
    for m in metas:
        for key in REQUIRED_METADATA:
            assert key in m, key
        for code in CONSTRAINT_CODES:
            assert isinstance(m[f"btsn_{code}"], bool)
        assert all(isinstance(v, (str, int, float, bool)) for v in m.values())
        assert m["total_chunks"] > m["chunk_index"] >= 0
    kb01 = [m for m in metas if m["doc_id"] == "KB01"]
    assert kb01[0]["kode_batasan_terkait"] == "B3,B4,G3"
    assert kb01[0]["btsn_B3"] and not kb01[0]["btsn_U6"]
    assert any(m["section_path"].endswith("3.2 Aturan Stacking") for m in kb01)


def test_id_deterministik(indexed, embedder, tmp_path):
    ids_a = set(indexed["collection"].get(include=[])["ids"])
    other = get_collection(get_client(tmp_path / "chroma2"), "kb_test_40_10")
    index_corpus(indexed["docs"], embedder, 40, 10, other)
    assert set(other.get(include=[])["ids"]) == ids_a
    assert all(i.count("::") == 2 for i in ids_a)


def test_persisten_setelah_client_dibuka_ulang(indexed, tmp_path):
    n = indexed["collection"].count()
    reopened = get_collection(get_client(tmp_path / "chroma"), "kb_test_40_10")
    assert reopened.count() == n
    assert reopened.metadata["hnsw:space"] == "cosine"


def test_parse_codes_dan_nama_collection():
    assert parse_codes("b3; G3, X9") == ["B3", "G3"]
    assert collection_name("me5base", "200_40") == "kb_me5base_200_40"
