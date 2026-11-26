import math

import pytest

from eval.metrics import hit_at_k, ndcg_at_k, recall_at_k, reciprocal_rank, unique_urls

RANKED = ["a", "b", "c", "d", "e"]


class TestUniqueUrls:
    def test_keeps_first_occurrence_order(self):
        assert unique_urls(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_empty(self):
        assert unique_urls([]) == []


class TestHitAtK:
    def test_found_within_k(self):
        assert hit_at_k(RANKED, {"c"}, k=3) == 1.0

    def test_found_only_after_k(self):
        assert hit_at_k(RANKED, {"c"}, k=2) == 0.0

    def test_any_expected_page_counts(self):
        assert hit_at_k(RANKED, {"x", "b"}, k=2) == 1.0

    def test_missing(self):
        assert hit_at_k(RANKED, {"x"}, k=5) == 0.0


class TestRecallAtK:
    def test_all_found(self):
        assert recall_at_k(RANKED, {"a", "c"}, k=3) == 1.0

    def test_half_found(self):
        assert recall_at_k(RANKED, {"a", "c"}, k=2) == 0.5

    def test_none_found(self):
        assert recall_at_k(RANKED, {"x", "y"}, k=5) == 0.0

    def test_k_larger_than_ranking(self):
        assert recall_at_k(["a"], {"a", "b"}, k=5) == 0.5


class TestReciprocalRank:
    def test_first_position(self):
        assert reciprocal_rank(RANKED, {"a"}) == 1.0

    def test_third_position(self):
        assert reciprocal_rank(RANKED, {"c"}) == pytest.approx(1 / 3)

    def test_uses_first_relevant_of_several(self):
        assert reciprocal_rank(RANKED, {"d", "b"}) == 0.5

    def test_not_found(self):
        assert reciprocal_rank(RANKED, {"x"}) == 0.0


class TestNdcgAtK:
    def test_perfect_single(self):
        assert ndcg_at_k(RANKED, {"a"}, k=5) == 1.0

    def test_single_at_rank_three(self):
        # DCG = 1/log2(3+1) = 0.5, IDCG = 1/log2(2) = 1
        assert ndcg_at_k(RANKED, {"c"}, k=5) == pytest.approx(0.5)

    def test_two_relevant_ranks_one_and_three(self):
        dcg = 1 / math.log2(2) + 1 / math.log2(4)  # 1.5
        idcg = 1 / math.log2(2) + 1 / math.log2(3)  # 1.6309
        assert ndcg_at_k(RANKED, {"a", "c"}, k=5) == pytest.approx(dcg / idcg)
        assert ndcg_at_k(RANKED, {"a", "c"}, k=5) == pytest.approx(0.9197, abs=1e-4)

    def test_relevant_outside_k_scores_zero(self):
        assert ndcg_at_k(RANKED, {"e"}, k=3) == 0.0

    def test_ideal_when_all_expected_on_top(self):
        assert ndcg_at_k(["a", "b", "x"], {"a", "b"}, k=5) == pytest.approx(1.0)

    def test_idcg_capped_by_k(self):
        # 3 expected pages but k=2: the ideal list has only 2 slots.
        assert ndcg_at_k(["a", "b", "x"], {"a", "b", "c"}, k=2) == pytest.approx(1.0)


class TestEmptyExpected:
    @pytest.mark.parametrize(
        "call",
        [
            lambda: hit_at_k(RANKED, set(), k=5),
            lambda: recall_at_k(RANKED, set(), k=5),
            lambda: reciprocal_rank(RANKED, set()),
            lambda: ndcg_at_k(RANKED, set(), k=5),
        ],
    )
    def test_raises(self, call):
        with pytest.raises(ValueError, match="expected"):
            call()
