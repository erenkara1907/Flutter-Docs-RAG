import json

import pytest

from rag.answer import (
    MAX_QUESTION_CHARS,
    NOT_FOUND_MESSAGE,
    answer_question,
    build_prompt,
    generate_answer,
    parse_reply,
    validate_question,
)
from rag.chunk import Chunk
from rag.pipeline import SearchResult
from rag.retrieve import Hit


def make_hits(n: int = 5) -> list[Hit]:
    return [
        Hit(
            chunk=Chunk(
                url=f"https://docs.flutter.dev/page{i}", title=f"Page {i}", section="ui", heading=f"H{i}", text=f"text {i}"
            ),
            score=1.0 - i / 10,
        )
        for i in range(n)
    ]


def reply(answer="Use Expanded.", used=(1,), found=True, **extra) -> str:
    return json.dumps({"answer": answer, "used_sources": list(used), "found_in_docs": found, **extra})


def urls(sources) -> list[str]:
    return [s.url.rsplit("/", 1)[1] for s in sources]


class TestParseReply:
    def test_valid_reply(self):
        parsed = parse_reply(reply("Use Expanded.", used=[2, 1]), n_sources=5)
        assert (parsed.answer, parsed.used_sources, parsed.found_in_docs) == ("Use Expanded.", [2, 1], True)

    def test_markdown_fence_is_accepted(self):
        assert parse_reply(f"```json\n{reply()}\n```", n_sources=5).found_in_docs is True

    def test_source_number_that_was_not_in_the_prompt_is_rejected(self):
        with pytest.raises(ValueError, match="6"):
            parse_reply(reply(used=[1, 6]), n_sources=5)

    @pytest.mark.parametrize("bad", [0, -1, 99])
    def test_numbers_outside_the_range_are_rejected(self, bad):
        with pytest.raises(ValueError):
            parse_reply(reply(used=[bad]), n_sources=5)

    def test_booleans_and_strings_are_not_source_numbers(self):
        for bad in (True, "1", 1.5):
            with pytest.raises(ValueError):
                parse_reply(json.dumps({"answer": "x", "used_sources": [bad], "found_in_docs": True}), n_sources=5)

    def test_an_answer_with_no_sources_is_rejected(self):
        with pytest.raises(ValueError, match="source"):
            parse_reply(reply(used=[]), n_sources=5)

    def test_a_blank_answer_is_rejected(self):
        with pytest.raises(ValueError):
            parse_reply(reply(answer="  "), n_sources=5)

    def test_repeated_numbers_are_collapsed(self):
        assert parse_reply(reply(used=[2, 2, 1, 2]), n_sources=5).used_sources == [2, 1]

    def test_when_not_found_stray_source_numbers_are_ignored(self):
        parsed = parse_reply(reply(answer="", used=[99], found=False), n_sources=5)
        assert parsed.found_in_docs is False and parsed.used_sources == []

    @pytest.mark.parametrize("raw", ["not json", "[1]", "{}", '{"answer": "x"}'])
    def test_malformed_replies_raise_value_error(self, raw):
        with pytest.raises(ValueError):
            parse_reply(raw, n_sources=5)


class TestBuildPrompt:
    def test_contains_question_and_numbered_passages(self):
        prompt = build_prompt("How do I scroll?", make_hits(2))
        assert "How do I scroll?" in prompt
        assert "[1] Page 0 > H0" in prompt and "text 1" in prompt and "[2] Page 1" in prompt

    def test_the_model_never_sees_urls(self):
        assert "https://" not in build_prompt("q", make_hits(3))

    def test_states_the_rules_and_the_reply_format(self):
        prompt = build_prompt("q", make_hits(1))
        for phrase in ("found_in_docs", "used_sources", "ONLY", "same language"):
            assert phrase in prompt


class TestGenerateAnswer:
    def test_urls_are_added_by_the_code_from_the_chosen_numbers(self):
        result = generate_answer("q", make_hits(), lambda p: reply(used=[3, 1]))
        assert result.status == "answered"
        assert urls(result.sources) == ["page2", "page0"]

    def test_a_url_invented_by_the_model_is_ignored(self):
        llm = lambda p: reply(used=[1], url="https://evil.example/x", sources=["https://evil.example/y"])
        result = generate_answer("q", make_hits(), llm)
        assert urls(result.sources) == ["page0"]
        assert "evil" not in result.model_dump_json()

    def test_two_chunks_of_the_same_page_give_one_source(self):
        hits = make_hits(3)
        hits[1] = hits[1].model_copy(update={"chunk": hits[1].chunk.model_copy(update={"url": hits[0].chunk.url})})
        result = generate_answer("q", hits, lambda p: reply(used=[1, 2, 3]))
        assert urls(result.sources) == ["page0", "page2"]

    def test_invalid_source_number_is_retried_once(self):
        replies = iter([reply(used=[9]), reply(used=[2])])
        calls = []

        def llm(prompt):
            calls.append(prompt)
            return next(replies)

        result = generate_answer("q", make_hits(), llm)
        assert len(calls) == 2
        assert result.status == "answered" and urls(result.sources) == ["page1"]

    def test_still_invalid_after_retry_returns_invalid_reply_without_sources(self):
        result = generate_answer("q", make_hits(), lambda p: reply(used=[9]))
        assert result.status == "invalid_reply"
        assert result.sources == [] and result.answer == NOT_FOUND_MESSAGE

    def test_not_found_lists_the_three_nearest_pages(self):
        result = generate_answer("q", make_hits(), lambda p: reply(answer="", used=[], found=False))
        assert result.status == "not_found"
        assert result.answer == NOT_FOUND_MESSAGE
        assert result.sources == []
        assert urls(result.related) == ["page0", "page1", "page2"]

    def test_related_pages_are_distinct(self):
        hits = make_hits(4)
        hits[1] = hits[1].model_copy(update={"chunk": hits[1].chunk.model_copy(update={"url": hits[0].chunk.url})})
        result = generate_answer("q", hits, lambda p: reply(answer="", used=[], found=False))
        assert urls(result.related) == ["page0", "page2", "page3"]


class TestValidateQuestion:
    def test_returns_the_stripped_question(self):
        assert validate_question("  How?  ") == "How?"

    def test_question_at_the_limit_is_allowed(self):
        assert len(validate_question("a" * MAX_QUESTION_CHARS)) == MAX_QUESTION_CHARS

    def test_too_long_question_is_rejected(self):
        with pytest.raises(ValueError, match="300"):
            validate_question("a" * (MAX_QUESTION_CHARS + 1))

    def test_blank_question_is_rejected(self):
        with pytest.raises(ValueError):
            validate_question("   ")


class TestAnswerQuestion:
    def searcher(self, hits=None, is_flutter=True, search_query=None):
        found = make_hits() if hits is None else hits
        return lambda q: SearchResult(hits=found, search_query=search_query, is_flutter_question=is_flutter)

    def test_happy_path_returns_an_answer_with_sources_and_the_search_query(self):
        result = answer_question("How?", self.searcher(search_query="how"), lambda p: reply(used=[1]))
        assert result.status == "answered" and result.search_query == "how"

    def test_non_flutter_question_stops_before_the_model_is_asked(self):
        def llm(prompt):
            raise AssertionError("must not be called")

        result = answer_question("pizza?", self.searcher(is_flutter=False), llm)
        assert result.status == "not_found" and result.answer == NOT_FOUND_MESSAGE

    def test_no_search_results_means_not_found_without_a_model_call(self):
        def llm(prompt):
            raise AssertionError("must not be called")

        assert answer_question("q", self.searcher(hits=[]), llm).status == "not_found"

    def test_overlong_question_is_rejected_before_any_work(self):
        def boom(q):
            raise AssertionError("must not search")

        with pytest.raises(ValueError):
            answer_question("a" * 301, boom, lambda p: "")
