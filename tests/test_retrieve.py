import numpy as np

from rag.chunk import Chunk
from rag.index import Index
from rag.retrieve import build_bm25, hybrid_search, rrf_fuse, search, tokenize, top_k_indices


def make_index(vectors: list[list[float]]) -> Index:
    chunks = [
        Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading=f"H{i}", text=f"t{i}")
        for i in range(len(vectors))
    ]
    m = np.array(vectors, dtype=np.float32)
    return Index(chunks=chunks, embeddings=m / np.linalg.norm(m, axis=1, keepdims=True))


class TestTopKIndices:
    def test_returns_indices_of_highest_scores_in_descending_order(self):
        scores = np.array([0.1, 0.9, 0.5, 0.7])
        assert list(top_k_indices(scores, 2)) == [1, 3]

    def test_k_larger_than_n_returns_all_sorted(self):
        assert list(top_k_indices(np.array([0.2, 0.8]), 5)) == [1, 0]

    def test_ties_keep_original_order(self):
        assert list(top_k_indices(np.array([0.5, 0.5, 0.5]), 2)) == [0, 1]

    def test_k_zero_returns_empty(self):
        assert len(top_k_indices(np.array([0.1, 0.2]), 0)) == 0


class TestTokenize:
    def test_lowercases_and_splits_on_punctuation(self):
        assert tokenize("ListView.builder(itemCount: 3)") == ["listview", "builder", "itemcount", "3"]

    def test_keeps_identifiers_with_underscores_whole(self):
        assert tokenize("_my_value") == ["_my_value"]

    def test_empty_text_gives_no_tokens(self):
        assert tokenize("  ... ") == []


class TestRrfFuse:
    def test_hand_computed_order(self):
        # items 0 and 2 tie at 1/61 + 1/63; item 1 scores 2/62, a hair lower
        assert rrf_fuse([[0, 1, 2], [2, 1, 0]]) == [0, 2, 1]

    def test_item_found_by_both_lists_beats_item_found_by_one(self):
        assert rrf_fuse([[5], [7, 5]]) == [5, 7]

    def test_empty_ranking_is_ignored(self):
        assert rrf_fuse([[3, 4], []]) == [3, 4]

    def test_no_rankings_give_empty_list(self):
        assert rrf_fuse([]) == []


def make_text_index(vectors: list[list[float]], texts: list[str]) -> Index:
    chunks = [
        Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading="", text=text)
        for i, text in enumerate(texts)
    ]
    m = np.array(vectors, dtype=np.float32)
    return Index(chunks=chunks, embeddings=m / np.linalg.norm(m, axis=1, keepdims=True))


class TestHybridSearch:
    # vector order for query [1, 0]: p0, p1, p3, p4, p2. Only p2 contains the rare word.
    VECTORS = [[1, 0], [0.9, 0.436], [0, 1], [0.8, 0.6], [0.6, 0.8]]
    TEXTS = ["about rows", "about columns", "the zzqwidget class", "about stacks", "about grids"]

    def index(self) -> Index:
        return make_text_index(self.VECTORS, self.TEXTS)

    def hybrid(self, query: str, k: int = 2):
        index = self.index()
        return hybrid_search(
            query, np.array([1.0, 0.0], dtype=np.float32), index, build_bm25(index.chunks), k=k, candidates=5
        )

    def test_exact_word_match_lifts_a_chunk_the_vectors_ranked_last(self):
        urls = [h.chunk.url.rsplit("/", 1)[1] for h in self.hybrid("zzqwidget")]
        assert urls == ["p2", "p0"]

    def test_query_without_any_keyword_match_falls_back_to_vector_order(self):
        urls = [h.chunk.url.rsplit("/", 1)[1] for h in self.hybrid("nothing matches", k=3)]
        assert urls == ["p0", "p1", "p3"]

    def test_returns_at_most_k_hits(self):
        assert len(self.hybrid("zzqwidget", k=1)) == 1


class TestSearch:
    def test_most_similar_chunk_is_first(self):
        index = make_index([[1, 0], [0, 1], [1, 1]])
        query = np.array([0.0, 1.0], dtype=np.float32)
        hits = search(query, index, k=3)
        assert hits[0].chunk.url.endswith("/p1")
        assert hits[0].score > hits[1].score >= hits[2].score

    def test_scores_are_cosine_similarity_for_normalized_vectors(self):
        index = make_index([[1, 0]])
        query = np.array([np.sqrt(0.5), np.sqrt(0.5)], dtype=np.float32)
        assert np.isclose(search(query, index, k=1)[0].score, np.sqrt(0.5), atol=1e-5)

    def test_returns_at_most_k_hits(self):
        index = make_index([[1, 0], [0, 1], [1, 1]])
        assert len(search(np.array([1.0, 0.0], dtype=np.float32), index, k=2)) == 2

    def test_k_larger_than_index_returns_all_chunks(self):
        index = make_index([[1, 0], [0, 1]])
        assert len(search(np.array([1.0, 0.0], dtype=np.float32), index, k=10)) == 2
