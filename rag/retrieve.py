"""Vector search: one matrix product, then pick the top-k scores."""

import logging
import re
import sys
from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict
from rank_bm25 import BM25Okapi

from rag.chunk import Chunk
from rag.config import load_config
from rag.embed import DEFAULT_CACHE_DIR, EMBEDDING_SPECS, EmbeddingCache, embed_queries, load_embedder
from rag.index import INDEX_ROOT, Index, read_index

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
DEFAULT_CANDIDATES = 20
RRF_K = 60  # the constant from the original RRF paper; damps the gap between top ranks
_TOKEN = re.compile(r"\w+")


class Hit(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk: Chunk
    score: float


def top_k_indices(scores: np.ndarray, k: int) -> np.ndarray:
    """Indices of the k highest scores, best first. Ties keep original order."""
    if k <= 0:
        return np.empty(0, dtype=np.int64)
    return np.argsort(-scores, kind="stable")[:k]


def search(query_vector: np.ndarray, index: Index, k: int = DEFAULT_TOP_K) -> list[Hit]:
    """Both sides have length 1, so the dot product IS the cosine similarity."""
    scores = index.embeddings @ query_vector
    return [Hit(chunk=index.chunks[i], score=float(scores[i])) for i in top_k_indices(scores, k)]


def tokenize(text: str) -> list[str]:
    """Lowercase words. Identifiers like `ListView` or `_my_value` stay whole, so exact names match."""
    return _TOKEN.findall(text.lower())


def build_bm25(chunks: list[Chunk]) -> BM25Okapi:
    return BM25Okapi([tokenize(chunk.text) for chunk in chunks])


def rrf_scores(rankings: list[list[int]], k: int = RRF_K) -> dict[int, float]:
    """Reciprocal Rank Fusion: every list gives an item 1 / (k + rank). Only ranks matter, not raw scores."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


def rrf_fuse(rankings: list[list[int]], k: int = RRF_K) -> list[int]:
    """Items ordered by fused score, best first. Ties keep first-seen order."""
    scores = rrf_scores(rankings, k)
    return sorted(scores, key=lambda item: -scores[item])


def hybrid_search(
    query: str,
    query_vector: np.ndarray,
    index: Index,
    bm25: BM25Okapi,
    k: int = DEFAULT_TOP_K,
    candidates: int = DEFAULT_CANDIDATES,
) -> list[Hit]:
    """Top `candidates` by vector and by BM25 keywords, merged with RRF, best k returned.

    Chunks with a BM25 score of 0 share no word with the query, so they are not candidates.
    """
    vector_ranking = [int(i) for i in top_k_indices(index.embeddings @ query_vector, candidates)]
    keyword_scores = bm25.get_scores(tokenize(query))
    keyword_ranking = [int(i) for i in top_k_indices(keyword_scores, candidates) if keyword_scores[i] > 0]

    scores = rrf_scores([vector_ranking, keyword_ranking])
    best = sorted(scores, key=lambda item: -scores[item])[:k]
    return [Hit(chunk=index.chunks[i], score=scores[i]) for i in best]


def bm25_search(query: str, index: Index, bm25: BM25Okapi, k: int = DEFAULT_TOP_K) -> list[Hit]:
    """Keyword-only search. Chunks that share no word with the query are never returned."""
    scores = bm25.get_scores(tokenize(query))
    return [Hit(chunk=index.chunks[i], score=float(scores[i])) for i in top_k_indices(scores, k) if scores[i] > 0]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(sys.argv) < 2:
        raise SystemExit('usage: python -m rag.retrieve "your question" [config]')
    query = sys.argv[1]
    config = load_config(sys.argv[2] if len(sys.argv) > 2 else "r0")
    spec = EMBEDDING_SPECS[config.embedding]

    index = read_index(Path(INDEX_ROOT) / config.name)
    query_vector = embed_queries([query], spec, load_embedder(spec, "query"), EmbeddingCache(DEFAULT_CACHE_DIR))[0]
    for rank, hit in enumerate(search(query_vector, index), start=1):
        label = hit.chunk.title + (f" > {hit.chunk.heading}" if hit.chunk.heading else "")
        logger.info("%d. [%.3f] %s\n   %s", rank, hit.score, label, hit.chunk.url)


if __name__ == "__main__":
    main()
