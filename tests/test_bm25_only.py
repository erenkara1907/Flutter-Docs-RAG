"""The BM25-only search path: no embedding model, no vectors. This is what the live site runs."""

import json

import numpy as np
import pytest
from pydantic import ValidationError

from rag.chunk import Chunk
from rag.config import RunConfig
from rag.embed import EmbeddingCache
from rag.index import Index, build_index, read_index
from rag.ingest import Page
from rag.pipeline import build_searcher
from rag.retrieve import bm25_search, build_bm25

# BM25 gives a word that is in half the corpus an idf of 0, so the corpus needs unrelated filler chunks
TEXTS = [
    "ListView shows a scrolling list", "Container adds padding", "Hero animates between routes",
    "ListView builder is lazy", "Navigator pushes pages", "Theme sets colors", "Form validates input",
    "Image loads pictures", "Text shows words", "Stack overlaps widgets",
]


def make_index() -> Index:
    chunks = [
        Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading="", text=text)
        for i, text in enumerate(TEXTS)
    ]
    return Index(chunks=chunks, embeddings=np.zeros((len(chunks), 0), dtype=np.float32))


def urls(hits) -> list[str]:
    return [h.chunk.url.rsplit("/p", 1)[1] for h in hits]


class TestConfig:
    def test_bm25_is_an_embedding_choice(self):
        assert RunConfig(name="x", embedding="bm25").embedding == "bm25"

    def test_hybrid_makes_no_sense_without_vectors(self):
        with pytest.raises(ValidationError, match="hybrid"):
            RunConfig(name="x", embedding="bm25", hybrid=True)


class TestBm25Search:
    def test_ranks_chunks_by_keyword_match(self):
        index = make_index()
        # both match once; BM25 length normalisation puts the shorter chunk (p3) first
        assert urls(bm25_search("listview", index, build_bm25(index.chunks), 2)) == ["3", "0"]

    def test_chunks_sharing_no_word_with_the_query_are_not_returned(self):
        index = make_index()
        assert urls(bm25_search("hero", index, build_bm25(index.chunks), 5)) == ["2"]

    def test_unmatched_query_returns_nothing(self):
        index = make_index()
        assert bm25_search("zzz", index, build_bm25(index.chunks), 5) == []


class TestPipeline:
    def search(self, config, tmp_path, llm=None):
        return build_searcher(config, make_index(), None, EmbeddingCache(tmp_path), None, llm)

    def test_searches_keywords_without_any_embedder(self, tmp_path):
        result = self.search(RunConfig(name="x", embedding="bm25", top_k=2), tmp_path)("listview")
        assert urls(result.hits) == ["3", "0"]

    def test_rewrite_feeds_the_rewritten_query_to_bm25(self, tmp_path):
        llm = lambda prompt: json.dumps({"search_query": "hero", "is_flutter_question": True})
        result = self.search(RunConfig(name="x", embedding="bm25", rewrite=True), tmp_path, llm)("bir animasyon sorusu")
        assert urls(result.hits) == ["2"] and result.search_query == "hero"


class TestMakeSearcher:
    def test_loading_a_bm25_config_writes_nothing_to_disk(self, tmp_path, monkeypatch):
        """The live server's file system is read-only: no cache folder may be created."""
        from rag import pipeline
        from rag.index import write_index

        write_index(tmp_path / "index" / "b", make_index().chunks, make_index().embeddings)
        monkeypatch.setattr(pipeline, "INDEX_ROOT", tmp_path / "index")
        monkeypatch.setattr(pipeline, "DEFAULT_CACHE_DIR", tmp_path / "no-cache-here")

        search = pipeline.make_searcher(RunConfig(name="b", embedding="bm25", top_k=2))

        assert urls(search("listview").hits) == ["3", "0"]
        assert not (tmp_path / "no-cache-here").exists()


class TestIndex:
    PAGE = Page(url="https://docs.flutter.dev/ui/layout", title="Layout", section="ui", text="## Row\n\nRows lay out children.")

    def test_building_needs_no_embedder_and_stores_no_vectors(self, tmp_path):
        config = RunConfig(name="b", chunker="heading", embedding="bm25")
        build_index(config, [self.PAGE], None, EmbeddingCache(tmp_path / "c"), "", tmp_path / "index")
        index = read_index(tmp_path / "index" / "b")
        assert len(index.chunks) >= 1 and index.embeddings.shape == (len(index.chunks), 0)
