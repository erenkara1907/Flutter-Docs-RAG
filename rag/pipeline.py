"""The search half of the system: question -> rewrite -> embed -> vector/hybrid search -> rerank.

Which parts are on is decided by a RunConfig. Used by the evaluation and by answer generation.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from rag.config import RunConfig
from rag.embed import (
    DEFAULT_CACHE_DIR,
    EMBEDDING_SPECS,
    Embedder,
    EmbeddingCache,
    EmbeddingSpec,
    embed_queries,
    load_embedder,
)
from rag.index import INDEX_ROOT, Index, read_index
from rag.llm import Llm, ollama_llm
from rag.rerank import rerank
from rag.retrieve import Hit, bm25_search, build_bm25, hybrid_search, search
from rag.rewrite import rewrite_query

LLM_SEED = 42  # same rewrites and rankings on every run, so ablation rows stay comparable


@dataclass(frozen=True)
class SearchResult:
    hits: list[Hit]
    search_query: str | None = None  # what was actually searched, when the question was rewritten
    is_flutter_question: bool = True  # False only when the rewrite step judged the question off-topic


Searcher = Callable[[str], SearchResult]


def build_searcher(
    config: RunConfig,
    index: Index,
    embedder: Embedder | None,
    cache: EmbeddingCache | None,
    spec: EmbeddingSpec | None,
    llm: Llm | None,
) -> Searcher:
    """Wire the parts together. Everything external is passed in, so tests can fake it.

    A 'bm25' config needs no embedder or spec (pass None): it searches by keywords only.
    """
    keywords_only = config.embedding == "bm25"
    bm25 = build_bm25(index.chunks) if config.hybrid or keywords_only else None
    fetch = config.candidates if config.rerank else config.top_k

    def search_question(question: str) -> SearchResult:
        rewrite = rewrite_query(question, llm) if config.rewrite else None
        search_query = rewrite.search_query if rewrite else question

        if keywords_only:
            hits = bm25_search(search_query, index, bm25, fetch)
        else:
            query_vector: np.ndarray = embed_queries([search_query], spec, embedder, cache)[0]
            if bm25 is None:
                hits = search(query_vector, index, fetch)
            else:
                hits = hybrid_search(search_query, query_vector, index, bm25, fetch, config.candidates)
        if config.rerank:
            hits = rerank(question, hits, llm, config.top_k)

        return SearchResult(
            hits=hits,
            search_query=search_query if rewrite else None,
            is_flutter_question=rewrite.is_flutter_question if rewrite else True,
        )

    return search_question


def make_searcher(config: RunConfig, llm: Llm | None = None) -> Searcher:
    """Load the config's index and models from disk. The dev LLM is local Ollama."""
    index = read_index(Path(INDEX_ROOT) / config.name)
    spec = EMBEDDING_SPECS.get(config.embedding)  # None for 'bm25'
    embedder = load_embedder(spec, "query") if spec else None
    if (config.rewrite or config.rerank) and llm is None:
        llm = ollama_llm(temperature=0.0, seed=LLM_SEED)
    cache = EmbeddingCache(DEFAULT_CACHE_DIR) if spec else None  # creating it makes a folder; the live server is read-only
    return build_searcher(config, index, embedder, cache, spec, llm)
