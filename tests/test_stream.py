import json

import pytest

from rag.answer import NOT_FOUND_MESSAGE
from rag.chunk import Chunk
from rag.pipeline import SearchResult
from rag.retrieve import Hit
from rag.stream import AnswerExtractor, stream_answer


def chunk(i: int) -> Chunk:
    return Chunk(url=f"https://docs.flutter.dev/p{i}", title=f"T{i}", section="ui", heading="", text=f"text {i}")


def searcher(n_hits=2, search_query="rewritten", is_flutter=True):
    hits = [Hit(chunk=chunk(i), score=1.0) for i in range(n_hits)]
    return lambda q: SearchResult(hits=hits, search_query=search_query, is_flutter_question=is_flutter)


def pieces(text: str, size: int):
    return [text[i : i + size] for i in range(0, len(text), size)]


def reply(answer="Use Expanded.", used=(1,), found=True) -> str:
    return json.dumps({"answer": answer, "used_sources": list(used), "found_in_docs": found})


def feed_all(raw: str, size: int) -> str:
    extractor = AnswerExtractor()
    return "".join(extractor.feed(p) for p in pieces(raw, size))


class TestAnswerExtractor:
    @pytest.mark.parametrize("size", [1, 2, 3, 7, 1000])
    def test_yields_the_answer_text_however_the_stream_is_cut(self, size):
        assert feed_all(reply("Use Expanded."), size) == "Use Expanded."

    @pytest.mark.parametrize("size", [1, 2, 5, 1000])
    def test_decodes_escapes_even_when_they_are_split_across_chunks(self, size):
        text = 'Line one\nLine "two"\tand a backslash \\ done'
        assert feed_all(reply(text), size) == text

    @pytest.mark.parametrize("size", [1, 3, 6, 1000])
    def test_decodes_unicode_including_surrogate_pairs(self, size):
        text = "Türkçe ığüşöç ✓ and an emoji \U0001F600"
        assert feed_all(json.dumps({"answer": text, "used_sources": [1], "found_in_docs": True}), size) == text

    @pytest.mark.parametrize("size", [1, 4, 1000])
    def test_a_key_order_with_the_answer_last_still_works(self, size):
        raw = json.dumps({"used_sources": [1], "found_in_docs": True, "answer": "late"})
        assert feed_all(raw, size) == "late"

    def test_nothing_is_yielded_before_the_answer_starts(self):
        extractor = AnswerExtractor()
        assert extractor.feed('{"used_sou') == "" and extractor.feed('rces": [1], "ans') == ""

    def test_text_after_the_closing_quote_is_ignored(self):
        assert feed_all('{"answer": "done", "used_sources": [1], "found_in_docs": true}', 5) == "done"

    def test_an_empty_answer_yields_nothing(self):
        assert feed_all(reply("", used=(), found=False), 3) == ""

    def test_garbage_does_not_raise(self):
        assert feed_all('{"answer": "bad \\u12', 4) == "bad "


def run(llm_streams, **kwargs):
    """Fake stream LLM: each call plays the next prepared list of chunks."""
    plays = iter(llm_streams)
    return list(stream_answer("question", kwargs.pop("search", searcher()), lambda prompt: iter(next(plays)), **kwargs))


class TestStreamAnswer:
    def test_sends_meta_then_tokens_then_the_final_answer(self):
        events = run([pieces(reply("Use Expanded."), 4)])
        assert events[0] == {"type": "meta", "search_query": "rewritten"}
        assert "".join(e["text"] for e in events if e["type"] == "token") == "Use Expanded."
        done = events[-1]
        assert done["type"] == "done" and done["answer"]["status"] == "answered"
        assert done["answer"]["sources"] == [{"title": "T0", "url": "https://docs.flutter.dev/p0"}]
        assert done["answer"]["search_query"] == "rewritten"

    def test_not_found_reply_ends_with_the_not_found_message_and_related_pages(self):
        done = run([pieces(reply("", used=(), found=False), 5)])[-1]["answer"]
        assert done["status"] == "not_found" and done["answer"] == NOT_FOUND_MESSAGE and len(done["related"]) == 2

    def test_off_topic_questions_never_reach_the_model(self):
        def boom(prompt):
            raise AssertionError("model must not run")

        events = list(stream_answer("pizza", searcher(is_flutter=False), boom))
        assert events[-1]["answer"]["status"] == "not_found" and not any(e["type"] == "token" for e in events)

    def test_a_search_without_hits_never_reaches_the_model(self):
        events = list(stream_answer("x", searcher(n_hits=0), lambda p: (_ for _ in ()).throw(AssertionError("no"))))
        assert events[-1]["answer"]["status"] == "not_found"

    def test_a_bad_first_reply_resets_the_text_and_retries(self):
        bad = pieces(reply("Wrong source.", used=(9,)), 6)  # passage 9 does not exist
        good = pieces(reply("Right."), 6)
        events = run([bad, good])
        types = [e["type"] for e in events]
        assert "reset" in types and types.index("reset") < len(types) - 2
        assert events[-1]["answer"]["answer"] == "Right."

    def test_two_bad_replies_end_as_invalid_reply(self):
        events = run([pieces("not json at all", 5), pieces("still not json", 5)])
        assert events[-1]["answer"]["status"] == "invalid_reply"

    def test_questions_are_validated_first(self):
        with pytest.raises(ValueError):
            list(stream_answer("   ", searcher(), lambda p: iter([])))

    def test_without_a_rewrite_there_is_no_search_query(self):
        events = run([pieces(reply(), 5)], search=searcher(search_query=None))
        assert events[0] == {"type": "meta", "search_query": None}
