import numpy as np

from rag.config import RunConfig
from rag.embed import (
    EMBEDDING_SPECS,
    EmbeddingCache,
    EmbeddingSpec,
    embed_queries,
    embed_texts,
    normalize,
    text_hash,
)


class FakeEmbedder:
    """Deterministic stand-in for a real model; records what it was asked to embed."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, texts: list[str]) -> np.ndarray:
        self.calls.append(list(texts))
        return np.array([[len(t), ord(t[0]), 1.0] for t in texts], dtype=np.float32)


class TestTextHash:
    def test_is_deterministic(self):
        assert text_hash("abc", "m") == text_hash("abc", "m")

    def test_differs_by_text_and_by_model(self):
        assert text_hash("abc", "m") != text_hash("abd", "m")
        assert text_hash("abc", "m1") != text_hash("abc", "m2")


class TestEmbeddingSpecs:
    def test_minilm_has_no_query_prefix(self):
        assert EMBEDDING_SPECS["minilm"].query_prefix == ""

    def test_bge_small_expects_the_retrieval_instruction_on_queries(self):
        spec = EMBEDDING_SPECS["bge-small"]
        assert spec.model_id == "BAAI/bge-small-en-v1.5"
        assert spec.query_prefix == "Represent this sentence for searching relevant passages: "

    def test_gemini_asks_for_768_dimensions(self):
        spec = EMBEDDING_SPECS["gemini"]
        assert (spec.provider, spec.model_id, spec.dimensions) == ("gemini", "gemini-embedding-001", 768)

    def test_dimensions_are_part_of_the_cache_key(self):
        assert EmbeddingSpec("m", dimensions=768).doc_cache_key != EmbeddingSpec("m", dimensions=3072).doc_cache_key

    def test_local_document_cache_key_is_unchanged(self):
        assert EmbeddingSpec("m").doc_cache_key == "m"

    def test_query_cache_key_differs_from_document_cache_key(self):
        spec = EmbeddingSpec("m")
        assert spec.query_cache_key != spec.doc_cache_key

    def test_every_spec_key_is_a_valid_config_value(self):
        for key in EMBEDDING_SPECS:
            RunConfig(name="x", embedding=key)


class TestEmbedQueries:
    SPEC = EmbeddingSpec(model_id="m", query_prefix="query: ")

    def test_prefix_is_added_before_the_model_sees_the_text(self, tmp_path):
        embedder = FakeEmbedder()
        embed_queries(["how?"], self.SPEC, embedder, EmbeddingCache(tmp_path))
        assert embedder.calls == [["query: how?"]]

    def test_query_and_document_with_same_text_do_not_share_cache_entries(self, tmp_path):
        cache = EmbeddingCache(tmp_path)
        embedder = FakeEmbedder()
        embed_texts(["how?"], embedder, cache, "m")
        embed_queries(["how?"], self.SPEC, embedder, cache)
        assert embedder.calls == [["how?"], ["query: how?"]]

    def test_query_vectors_live_under_the_query_cache_key(self, tmp_path):
        cache = EmbeddingCache(tmp_path)
        embed_queries(["how?"], self.SPEC, FakeEmbedder(), cache)
        assert cache.has(text_hash("query: how?", self.SPEC.query_cache_key))
        assert not cache.has(text_hash("query: how?", self.SPEC.doc_cache_key))

    def test_second_identical_query_is_served_from_cache(self, tmp_path):
        cache = EmbeddingCache(tmp_path)
        embedder = FakeEmbedder()
        embed_queries(["how?"], self.SPEC, embedder, cache)
        embed_queries(["how?"], self.SPEC, embedder, cache)
        assert len(embedder.calls) == 1


class TestNormalize:
    def test_rows_have_unit_length(self):
        out = normalize(np.array([[3.0, 4.0], [1.0, 1.0]], dtype=np.float32))
        assert np.allclose(np.linalg.norm(out, axis=1), 1.0)

    def test_zero_vector_stays_zero_without_nan(self):
        out = normalize(np.zeros((1, 3), dtype=np.float32))
        assert not np.isnan(out).any()
        assert np.allclose(out, 0.0)

    def test_does_not_mutate_input(self):
        original = np.array([[3.0, 4.0]], dtype=np.float32)
        normalize(original)
        assert np.allclose(original, [[3.0, 4.0]])


class TestEmbedTexts:
    def test_returns_normalized_rows_in_input_order(self, tmp_path):
        cache = EmbeddingCache(tmp_path)
        out = embed_texts(["bb", "a"], FakeEmbedder(), cache, "m")
        assert out.shape == (2, 3)
        assert np.allclose(np.linalg.norm(out, axis=1), 1.0)
        expected_first = normalize(np.array([[2, ord("b"), 1.0]], dtype=np.float32))[0]
        assert np.allclose(out[0], expected_first)

    def test_second_call_hits_cache_and_skips_embedder(self, tmp_path):
        cache, embedder = EmbeddingCache(tmp_path), FakeEmbedder()
        first = embed_texts(["x", "yy"], embedder, cache, "m")
        second = embed_texts(["x", "yy"], embedder, cache, "m")
        assert len(embedder.calls) == 1
        assert np.allclose(first, second)

    def test_only_missing_texts_are_embedded(self, tmp_path):
        cache, embedder = EmbeddingCache(tmp_path), FakeEmbedder()
        embed_texts(["x"], embedder, cache, "m")
        embed_texts(["x", "yy"], embedder, cache, "m")
        assert embedder.calls[1] == ["yy"]

    def test_duplicate_texts_are_embedded_once(self, tmp_path):
        embedder = FakeEmbedder()
        out = embed_texts(["a", "a"], embedder, EmbeddingCache(tmp_path), "m")
        assert embedder.calls == [["a"]]
        assert np.allclose(out[0], out[1])

    def test_cache_persists_across_instances(self, tmp_path):
        embed_texts(["x"], FakeEmbedder(), EmbeddingCache(tmp_path), "m")
        embedder = FakeEmbedder()
        embed_texts(["x"], embedder, EmbeddingCache(tmp_path), "m")
        assert embedder.calls == []

    def test_different_model_name_does_not_share_cache(self, tmp_path):
        cache, embedder = EmbeddingCache(tmp_path), FakeEmbedder()
        embed_texts(["x"], embedder, cache, "m1")
        embed_texts(["x"], embedder, cache, "m2")
        assert len(embedder.calls) == 2

    def test_empty_input_returns_empty_matrix(self, tmp_path):
        out = embed_texts([], FakeEmbedder(), EmbeddingCache(tmp_path), "m")
        assert out.shape[0] == 0
