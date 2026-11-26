import json

import pytest

from rag.chunk import Chunk
from rag.rerank import MAX_CHUNK_CHARS, build_prompt, parse_ranking, rerank
from rag.retrieve import Hit


def make_hits(n: int) -> list[Hit]:
    return [
        Hit(
            chunk=Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading=f"H{i}", text=f"body {i}"),
            score=1.0 - i / 100,
        )
        for i in range(n)
    ]


def reply(ranking) -> str:
    return json.dumps({"ranking": ranking})


def urls(hits: list[Hit]) -> list[str]:
    return [h.chunk.url.rsplit("/", 1)[1] for h in hits]


class TestParseRanking:
    def test_converts_one_based_numbers_to_zero_based_indices(self):
        assert parse_ranking(reply([3, 1, 2]), n_candidates=5, top_k=5) == [2, 0, 1]

    def test_keeps_at_most_top_k(self):
        assert parse_ranking(reply([4, 3, 2, 1]), n_candidates=5, top_k=2) == [3, 2]

    def test_markdown_fence_is_accepted(self):
        assert parse_ranking(f"```json\n{reply([2])}\n```", n_candidates=3, top_k=3) == [1]

    def test_out_of_range_and_non_integer_entries_are_dropped(self):
        assert parse_ranking(reply([9, 0, -1, "2", 2.5, True, 2]), n_candidates=5, top_k=5) == [1]

    def test_repeated_numbers_are_dropped(self):
        assert parse_ranking(reply([2, 2, 1, 2]), n_candidates=5, top_k=5) == [1, 0]

    @pytest.mark.parametrize(
        "raw",
        ["not json", "[1, 2]", "{}", reply("1,2,3"), reply([]), reply([99, 100])],
    )
    def test_unusable_replies_raise_value_error(self, raw):
        with pytest.raises(ValueError):
            parse_ranking(raw, n_candidates=5, top_k=5)


class TestBuildPrompt:
    def test_lists_numbered_candidates_with_titles(self):
        prompt = build_prompt("how to scroll?", make_hits(2), top_k=1)
        assert "how to scroll?" in prompt
        assert "[1] T0 > H0" in prompt and "[2] T1 > H1" in prompt

    def test_asks_for_the_requested_number_of_results(self):
        assert "5" in build_prompt("q", make_hits(3), top_k=5)

    def test_long_chunks_are_cut_to_keep_the_prompt_small(self):
        hit = make_hits(1)[0]
        long_hit = Hit(chunk=hit.chunk.model_copy(update={"text": "x" * 5000}), score=0.5)
        assert "x" * (MAX_CHUNK_CHARS + 1) not in build_prompt("q", [long_hit], top_k=1)


class TestRerank:
    def test_reorders_by_the_models_ranking(self):
        result = rerank("q", make_hits(5), lambda p: reply([5, 3]), top_k=2)
        assert urls(result) == ["p4", "p2"]

    def test_missing_slots_are_filled_in_original_order(self):
        result = rerank("q", make_hits(5), lambda p: reply([4]), top_k=3)
        assert urls(result) == ["p3", "p0", "p1"]

    def test_bad_first_reply_is_retried(self):
        replies = iter(["garbage", reply([2, 1])])
        assert urls(rerank("q", make_hits(3), lambda p: next(replies), top_k=2)) == ["p1", "p0"]

    def test_falls_back_to_the_original_order_when_every_attempt_fails(self):
        assert urls(rerank("q", make_hits(5), lambda p: "garbage", top_k=3)) == ["p0", "p1", "p2"]

    def test_keeps_the_original_hit_objects(self):
        hits = make_hits(3)
        assert rerank("q", hits, lambda p: reply([3]), top_k=1)[0] is hits[2]

    def test_empty_candidates_need_no_model_call(self):
        def llm(prompt):
            raise AssertionError("should not be called")

        assert rerank("q", [], llm, top_k=5) == []
