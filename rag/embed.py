"""Text -> unit-length vectors. Every embedding is cached on disk by text hash."""

import hashlib
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path("data/cache/embeddings")
ENCODE_BATCH_SIZE = 64
EMBED_CALL_SIZE = 256

Embedder = Callable[[list[str]], np.ndarray]


@dataclass(frozen=True)
class EmbeddingSpec:
    model_id: str
    query_prefix: str = ""  # text some models expect in front of search queries (never chunks)
    provider: Literal["local", "gemini"] = "local"
    dimensions: int | None = None  # None: the model's native size

    @property
    def doc_cache_key(self) -> str:
        """Cache namespace for chunk vectors. Dimensions change the vectors, so they are in the key."""
        return f"{self.model_id}@{self.dimensions}" if self.dimensions else self.model_id

    @property
    def query_cache_key(self) -> str:
        """Query vectors can differ from chunk vectors for the same text (Gemini task types)."""
        return f"{self.doc_cache_key}#query"


# keys are the values allowed in RunConfig.embedding
EMBEDDING_SPECS = {
    "minilm": EmbeddingSpec("sentence-transformers/all-MiniLM-L6-v2"),
    "bge-small": EmbeddingSpec(
        "BAAI/bge-small-en-v1.5",
        query_prefix="Represent this sentence for searching relevant passages: ",
    ),
    "gemini": EmbeddingSpec("gemini-embedding-001", provider="gemini", dimensions=768),
}

GEMINI_TASK_TYPES = {"document": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


def text_hash(text: str, model: str) -> str:
    """Cache key. The model name is part of it: two models never share vectors."""
    return hashlib.sha256(f"{model}\0{text}".encode()).hexdigest()


def normalize(matrix: np.ndarray) -> np.ndarray:
    """Scale every row to length 1 (zero rows stay zero). Returns a new array."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return (matrix / np.where(norms == 0, 1.0, norms)).astype(np.float32)


class EmbeddingCache:
    """One .npy file per text hash; writes are atomic so an interrupted run can resume."""

    def __init__(self, directory: Path) -> None:
        self._directory = Path(directory)
        self._directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._directory / f"{key}.npy"

    def has(self, key: str) -> bool:
        return self._path(key).exists()

    def get(self, key: str) -> np.ndarray:
        return np.load(self._path(key))

    def put(self, key: str, vector: np.ndarray) -> None:
        tmp = self._directory / f"{key}.tmp.npy"
        np.save(tmp, np.asarray(vector, dtype=np.float32))
        os.replace(tmp, self._path(key))


def embed_texts(
    texts: list[str],
    embedder: Embedder,
    cache: EmbeddingCache,
    model: str,
) -> np.ndarray:
    """Return one normalized row per input text, in input order.

    Only texts missing from the cache reach `embedder`; duplicates are embedded once.
    """
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    keys = [text_hash(t, model) for t in texts]
    missing: dict[str, str] = {}
    for key, text in zip(keys, texts):
        if key not in missing and not cache.has(key):
            missing[key] = text

    pending = list(missing.items())
    for start in range(0, len(pending), EMBED_CALL_SIZE):
        batch = pending[start : start + EMBED_CALL_SIZE]
        vectors = embedder([text for _, text in batch])
        if len(vectors) != len(batch):
            raise ValueError(f"Embedder returned {len(vectors)} vectors for {len(batch)} texts")
        for (key, _), vector in zip(batch, vectors):
            cache.put(key, vector)
        logger.info("embedded %d/%d new texts", min(start + EMBED_CALL_SIZE, len(pending)), len(pending))

    return normalize(np.stack([cache.get(key) for key in keys]))


def embed_queries(
    queries: list[str],
    spec: EmbeddingSpec,
    embedder: Embedder,
    cache: EmbeddingCache,
) -> np.ndarray:
    """Embed search queries. The prefix is part of the text, so it is part of the cache key."""
    return embed_texts([spec.query_prefix + q for q in queries], embedder, cache, spec.query_cache_key)


def load_embedder(spec: EmbeddingSpec, task: Literal["document", "query"] = "document") -> Embedder:
    """Embedder for chunks (`task="document"`) or questions (`task="query"`).

    Local models are the same for both. sentence-transformers is imported lazily (dev-only dependency).
    """
    if spec.provider == "gemini":
        from rag.gemini import gemini_embedder

        return gemini_embedder(spec.model_id, spec.dimensions, GEMINI_TASK_TYPES[task])

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(spec.model_id)

    def embed(texts: list[str]) -> np.ndarray:
        return model.encode(
            texts,
            batch_size=ENCODE_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    return embed
