import json

import pytest

from rag.rewrite import Rewrite, build_prompt, parse_rewrite, rewrite_query


def reply(query="make a list scroll", is_flutter=True) -> str:
    return json.dumps({"search_query": query, "is_flutter_question": is_flutter})


class TestParseRewrite:
    def test_valid_reply(self):
        assert parse_rewrite(reply("ListView builder")) == Rewrite(
            search_query="ListView builder", is_flutter_question=True
        )

    def test_json_wrapped_in_markdown_fence_is_accepted(self):
        assert parse_rewrite(f"```json\n{reply('x y')}\n```").search_query == "x y"

    def test_query_is_stripped(self):
        assert parse_rewrite(reply("  ListView  ")).search_query == "ListView"

    def test_not_flutter_flag_is_kept(self):
        assert parse_rewrite(reply("pizza", is_flutter=False)).is_flutter_question is False

    @pytest.mark.parametrize(
        "raw",
        [
            "not json at all",
            "[1, 2]",
            '{"search_query": "x"}',
            '{"is_flutter_question": true}',
            reply("   "),
            reply("word " * 100),
        ],
    )
    def test_unusable_replies_raise_value_error(self, raw):
        with pytest.raises(ValueError):
            parse_rewrite(raw)


class TestBuildPrompt:
    def test_contains_the_question_verbatim(self):
        assert "Bir listeyi nasıl kaydırırım?" in build_prompt("Bir listeyi nasıl kaydırırım?")

    def test_asks_for_english_and_json(self):
        prompt = build_prompt("q")
        assert "English" in prompt and "search_query" in prompt and "is_flutter_question" in prompt


class TestRewriteQuery:
    def test_returns_the_models_rewrite(self):
        assert rewrite_query("soru", lambda p: reply("scroll list")).search_query == "scroll list"

    def test_bad_first_reply_is_retried(self):
        replies = iter(["garbage", reply("scroll list")])
        assert rewrite_query("soru", lambda p: next(replies)).search_query == "scroll list"

    def test_falls_back_to_the_original_question_when_every_attempt_fails(self):
        result = rewrite_query("Bir liste nasıl kaydırılır?", lambda p: "garbage")
        assert result == Rewrite(search_query="Bir liste nasıl kaydırılır?", is_flutter_question=True)

    def test_llm_is_called_once_per_attempt(self):
        calls = []

        def llm(prompt):
            calls.append(prompt)
            return "garbage"

        rewrite_query("q", llm, attempts=3)
        assert len(calls) == 3
