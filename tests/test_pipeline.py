import json

import numpy as np

from rag.chunk import Chunk
from rag.config import RunConfig
from rag.embed import EmbeddingCache, EmbeddingSpec
from rag.index import Index
from rag.pipeline import build_searcher

SPEC = EmbeddingSpec(model_id="fake")


def fake_embedder(texts):
    """'alpha' texts point one way, everything else the other way."""
    return np.array([[1.0, 0.0] if "alpha" in t else [0.0, 1.0] for t in texts], dtype=np.float32)


def make_index() -> Index:
    chunks = [
        Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading="", text=text)
        for i, text in enumerate(["alpha one", "beta two", "beta three", "alpha four"])
    ]
    vectors = fake_embedder([c.text for c in chunks])
    return Index(chunks=chunks, embeddings=vectors)


def searcher(config: RunConfig, llm=None, tmp_path=None):
    return build_searcher(config, make_index(), fake_embedder, EmbeddingCache(tmp_path), SPEC, llm)


def page_numbers(result) -> list[str]:
    return [h.chunk.url.rsplit("/p", 1)[1] for h in result.hits]


class TestPlainVectorSearch:
    def test_searches_the_question_as_written(self, tmp_path):
        result = searcher(RunConfig(name="x", top_k=2), tmp_path=tmp_path)("alpha question")
        assert page_numbers(result) == ["0", "3"]
        assert result.search_query is None

    def test_returns_at_most_top_k_hits(self, tmp_path):
        assert len(searcher(RunConfig(name="x", top_k=3), tmp_path=tmp_path)("alpha").hits) == 3


class TestRewrite:
    def rewriting_llm(self, query="alpha", is_flutter=True):
        return lambda prompt: json.dumps({"search_query": query, "is_flutter_question": is_flutter})

    def test_searches_the_rewritten_query(self, tmp_path):
        config = RunConfig(name="x", top_k=2, rewrite=True)
        result = searcher(config, self.rewriting_llm("alpha"), tmp_path)("tamamen alakasiz kelimeler")
        assert page_numbers(result) == ["0", "3"]
        assert result.search_query == "alpha"

    def test_flutter_flag_is_passed_on(self, tmp_path):
        config = RunConfig(name="x", rewrite=True)
        result = searcher(config, self.rewriting_llm("pizza", is_flutter=False), tmp_path)("pizza?")
        assert result.is_flutter_question is False

    def test_without_rewrite_the_question_is_assumed_to_be_about_flutter(self, tmp_path):
        assert searcher(RunConfig(name="x"), tmp_path=tmp_path)("anything").is_flutter_question is True


class TestRerank:
    def llm(self, prompt):
        if "ranking" in prompt:
            return json.dumps({"ranking": [4, 3]})  # candidate numbers, 1-based
        return json.dumps({"search_query": "alpha", "is_flutter_question": True})

    def test_rerank_picks_from_the_wider_candidate_list(self, tmp_path):
        config = RunConfig(name="x", rewrite=True, rerank=True, top_k=2, candidates=4)
        result = searcher(config, self.llm, tmp_path)("alpha")
        # vector order is p0, p3, p1, p2; the model prefers candidates 4 and 3 = p2, p1
        assert page_numbers(result) == ["2", "1"]

    def test_rerank_sees_the_original_question_not_the_rewritten_one(self, tmp_path):
        prompts = []

        def llm(prompt):
            prompts.append(prompt)
            return self.llm(prompt)

        config = RunConfig(name="x", rewrite=True, rerank=True, top_k=2, candidates=4)
        searcher(config, llm, tmp_path)("soru metni burada")
        rerank_prompt = next(p for p in prompts if "ranking" in p)
        assert "soru metni burada" in rerank_prompt
