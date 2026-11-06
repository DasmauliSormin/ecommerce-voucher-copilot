"""Pembungkus model embedding.

Embedding dihitung SENDIRI (bukan lewat embedding_function bawaan ChromaDB)
agar kita mengontrol: prefix "query: "/"passage: " untuk E5, normalisasi L2,
batch size, dan penghitungan token dengan tokenizer model yang sebenarnya.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Protocol

import numpy as np

from .config import EMBED_BATCH_SIZE, MODELS, ModelSpec

logger = logging.getLogger(__name__)


class Embedder(Protocol):
    key: str
    name: str

    @property
    def dimension(self) -> int: ...

    @property
    def max_seq_length(self) -> int: ...

    def embed_passages(self, texts: list[str]) -> np.ndarray: ...

    def embed_queries(self, texts: list[str]) -> np.ndarray: ...

    def count_tokens(self, texts: list[str], as_passage: bool = True) -> list[int]: ...


class SentenceTransformerEmbedder:
    """Model Sentence-Transformers dengan embedding ternormalisasi (norma L2 = 1)."""

    def __init__(self, spec: ModelSpec, device: str | None = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "sentence-transformers belum terpasang. Jalankan: uv add sentence-transformers"
            ) from exc
        self.spec = spec
        self.key = spec.key
        self.name = spec.hf_name
        try:
            self._model = SentenceTransformer(spec.hf_name, device=device)
        except Exception as exc:  # jaringan, nama model salah, dsb.
            raise RuntimeError(
                f"Gagal memuat model '{spec.hf_name}'. Periksa koneksi internet atau nama model. Detail: {exc}"
            ) from exc

    @property
    def dimension(self) -> int:
        getter = (
            getattr(self._model, "get_embedding_dimension", None)
            or self._model.get_sentence_embedding_dimension
        )
        return int(getter())

    @property
    def max_seq_length(self) -> int:
        return int(self._model.max_seq_length)

    def _encode(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(
            texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 64,
        )
        return vectors.astype(np.float32)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return self._encode([self.spec.passage_prefix + t for t in texts])

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self._encode([self.spec.query_prefix + t for t in texts])

    def count_tokens(self, texts: list[str], as_passage: bool = True) -> list[int]:
        """Jumlah token SEBENARNYA (termasuk token spesial dan prefix), tanpa truncation."""
        prefix = self.spec.passage_prefix if as_passage else self.spec.query_prefix
        tok = self._model.tokenizer
        return [
            len(tok(prefix + t, add_special_tokens=True, truncation=False)["input_ids"])
            for t in texts
        ]


class HashingEmbedder:
    """Embedder deterministik berbasis hashing kata, HANYA untuk unit test.

    Tidak membutuhkan unduhan model sehingga test cepat dan offline.
    Vektor tetap dinormalisasi L2 seperti embedder sungguhan.
    """

    def __init__(self, dim: int = 256, max_len: int = 512) -> None:
        self.key = "hash"
        self.name = "hashing-test-embedder"
        self._dim = dim
        self._max_len = max_len

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def max_seq_length(self) -> int:
        return self._max_len

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self._dim, dtype=np.float32)
        for tok in re.findall(r"\w+", text.lower()):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self._dim] += 1.0 if (h >> 8) % 2 else -1.0
        norm = np.linalg.norm(v)
        return v / norm if norm else v

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return (
            np.stack([self._vec(t) for t in texts])
            if texts
            else np.zeros((0, self._dim), np.float32)
        )

    def embed_queries(self, texts: list[str]) -> np.ndarray:
        return self.embed_passages(texts)

    def count_tokens(self, texts: list[str], as_passage: bool = True) -> list[int]:
        return [len(t.split()) + 2 for t in texts]


_CACHE: dict[str, SentenceTransformerEmbedder] = {}


def get_embedder(model_key: str) -> SentenceTransformerEmbedder:
    """Memuat model sekali per proses (model cukup besar, jangan dimuat ulang)."""
    if model_key not in MODELS:
        raise KeyError(f"Model '{model_key}' tidak dikenal. Pilihan: {sorted(MODELS)}")
    if model_key not in _CACHE:
        logger.info("Memuat model %s ...", MODELS[model_key].hf_name)
        _CACHE[model_key] = SentenceTransformerEmbedder(MODELS[model_key])
    return _CACHE[model_key]


def count_parameters(embedder) -> int | None:
    """Jumlah parameter model (proksi ukuran model); None untuk embedder uji."""
    model = getattr(embedder, "_model", None)
    if model is None:
        return None
    return int(sum(p.numel() for p in model.parameters()))
