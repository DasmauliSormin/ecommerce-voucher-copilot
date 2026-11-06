"""Test chunker: kalimat utuh, overlap benar, section path, pemecah kalimat."""

from __future__ import annotations

import pytest
from _kb_samples import DOC_STACKING

from ecommerce_voucher_copilot.knowledge_base.chunker import (
    _paragraph_units,
    chunk_document,
    chunk_section,
    split_sections,
    split_sentences,
)

LONG_SECTION = "## 5. Prosedur\n" + " ".join(
    f"Langkah {i} dilakukan oleh petugas pemasaran sebelum kampanye promo diluncurkan."
    for i in range(1, 31)
)


def test_pemecah_kalimat_melindungi_singkatan_dan_angka():
    text = "Minimum belanja Rp50.000. Lihat No. 3 dan Pasal 3.2 untuk rinciannya, dll. Voucher berlaku."
    assert split_sentences(text) == [
        "Minimum belanja Rp50.000.",
        "Lihat No. 3 dan Pasal 3.2 untuk rinciannya, dll. Voucher berlaku.",
    ]


def test_penanda_butir_tidak_dianggap_kalimat():
    assert split_sentences("1. Voucher toko berlaku. Kuota terbatas.") == [
        "1. Voucher toko berlaku.",
        "Kuota terbatas.",
    ]


def test_section_path_mengikuti_heading_bertingkat():
    sections = split_sections(
        DOC_STACKING, title="Kebijakan Umum Voucher dan Aturan Penggabungan"
    )
    paths = [" > ".join(s.path) for s in sections]
    assert "3. Ketentuan > 3.2 Aturan Stacking" in paths
    assert "4. Sanksi" in paths  # heading level-2 baru menutup "3. Ketentuan"
    assert all(
        "Kebijakan Umum Voucher" not in p for p in paths
    )  # judul H1 tidak diulang


@pytest.mark.parametrize("size,overlap", [(20, 5), (40, 10), (60, 15)])
def test_chunker_tidak_memutus_kalimat(size, overlap):
    chunks = chunk_document(LONG_SECTION, size, overlap)
    sentences = [
        s
        for u in _paragraph_units(LONG_SECTION.split("\n", 1)[1])
        for s in split_sentences(u)
    ]
    for sent in sentences:
        # Setiap kalimat muncul UTUH di minimal satu chunk.
        assert any(sent in c.text for c in chunks), sent
    for c in chunks:
        assert c.word_count <= size
        assert not c.has_word_split
        assert c.text.endswith(".")


def test_overlap_berupa_kalimat_ekor_chunk_sebelumnya():
    sentences = [
        f"Kalimat nomor {i} berisi tujuh kata ini." for i in range(1, 13)
    ]  # 7 kata/kalimat
    chunks = chunk_section(sentences, size=30, overlap=10)
    texts = [t for t, _, _ in chunks]
    for prev, nxt in zip(texts, texts[1:]):
        prev_sents = split_sentences(prev)
        nxt_sents = split_sentences(nxt)
        # Kalimat terakhir chunk sebelumnya (7 kata <= overlap 10) mengawali chunk berikutnya.
        assert nxt_sents[0] == prev_sents[-1]
        assert (
            nxt_sents[1] not in prev_sents
        )  # hanya satu kalimat yang diulang (14 kata > 10)


def test_overlap_tidak_pernah_melebihi_batas():
    sentences = [f"Kalimat {i} pendek." for i in range(40)]
    for size, overlap in [(10, 3), (25, 8), (50, 20)]:
        chunks = chunk_section(sentences, size, overlap)
        texts = [t for t, _, _ in chunks]
        for prev, nxt in zip(texts, texts[1:]):
            shared = [s for s in split_sentences(nxt) if s in split_sentences(prev)]
            assert sum(len(s.split()) for s in shared) <= overlap


def test_kalimat_super_panjang_dipotong_kata_dan_ditandai():
    sent = " ".join(["kata"] * 50) + "."
    chunks = chunk_document("## A\n" + sent, size=20, overlap=5)
    assert all(c.word_count <= 20 for c in chunks)
    assert all(c.has_word_split for c in chunks)


def test_chunk_tidak_melintasi_section():
    chunks = chunk_document(
        DOC_STACKING,
        size=200,
        overlap=40,
        title="Kebijakan Umum Voucher dan Aturan Penggabungan",
    )
    stacking = [c for c in chunks if c.section_path.endswith("3.2 Aturan Stacking")]
    assert len(stacking) == 1
    assert "Penyalahgunaan" not in stacking[0].text
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_parameter_tidak_valid_ditolak():
    with pytest.raises(ValueError):
        chunk_section(["a."], size=10, overlap=10)
