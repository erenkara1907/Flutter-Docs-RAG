import json

import pytest

from rag.chunk import Chunk
from eval.make_candidates import (
    build_prompt,
    generate_candidates,
    is_eligible,
    lexical_overlap,
    parse_candidate,
    sample_balanced,
)

LONG_TEXT = "Flutter widgets compose into layouts and trees of objects. " * 12


def make_chunk(url="https://docs.flutter.dev/ui/a", section="ui", text=LONG_TEXT, heading="H") -> Chunk:
    return Chunk(url=url, title="T", section=section, heading=heading, text=text)


def valid_json(question="How do I center a widget?", answer="Wrap it in Center.") -> str:
    return json.dumps({"question": question, "answer": answer})


class TestIsEligible:
    def test_normal_prose_chunk_is_eligible(self):
        assert is_eligible(make_chunk())

    def test_too_short_chunk_is_rejected(self):
        assert not is_eligible(make_chunk(text="Short text."))

    def test_too_long_chunk_is_rejected(self):
        assert not is_eligible(make_chunk(text="word " * 600))

    def test_mostly_code_chunk_is_rejected(self):
        code = "```dart\n" + "final a = Text('x');\n" * 60 + "```\n" + "A bit of prose. " * 3
        assert not is_eligible(make_chunk(text=code))

    def test_release_notes_pages_are_rejected(self):
        chunk = make_chunk(url="https://docs.flutter.dev/tools/devtools/release-notes/release-notes-2.11.2")
        assert not is_eligible(chunk)


class TestSampleBalanced:
    def _pool(self):
        pool = [make_chunk(url=f"https://docs.flutter.dev/ui/p{i}", section="ui") for i in range(20)]
        pool += [make_chunk(url=f"https://docs.flutter.dev/tools/p{i}", section="tools") for i in range(3)]
        return pool

    def test_is_deterministic_for_same_seed(self):
        assert sample_balanced(self._pool(), 6, seed=1) == sample_balanced(self._pool(), 6, seed=1)

    def test_different_seed_gives_different_order(self):
        assert sample_balanced(self._pool(), 6, seed=1) != sample_balanced(self._pool(), 6, seed=2)

    def test_round_robin_mixes_sections_early(self):
        picked = sample_balanced(self._pool(), 4, seed=0)
        assert {c.section for c in picked[:2]} == {"ui", "tools"}

    def test_at_most_one_chunk_per_page(self):
        pool = [make_chunk(url="https://docs.flutter.dev/ui/same", heading=f"H{i}") for i in range(5)]
        assert len(sample_balanced(pool, 5, seed=0)) == 1

    def test_returns_fewer_when_pool_is_small(self):
        assert len(sample_balanced(self._pool(), 100, seed=0)) == 23

    def test_does_not_mutate_input(self):
        pool = self._pool()
        snapshot = list(pool)
        sample_balanced(pool, 5, seed=0)
        assert pool == snapshot


class TestBuildPrompt:
    def test_contains_chunk_text_and_json_instruction(self):
        prompt = build_prompt(make_chunk(text="UNIQUE_MARKER body"))
        assert "UNIQUE_MARKER body" in prompt
        assert "JSON" in prompt and "question" in prompt and "answer" in prompt


class TestParseCandidate:
    def test_parses_valid_json(self):
        c = parse_candidate(valid_json())
        assert c.question == "How do I center a widget?" and c.answer == "Wrap it in Center."

    def test_strips_markdown_code_fences(self):
        assert parse_candidate(f"```json\n{valid_json()}\n```").question.startswith("How")

    @pytest.mark.parametrize("raw", ["not json", "{}", '{"question": "q"}', '{"question": "", "answer": "a"}'])
    def test_rejects_invalid_or_incomplete(self, raw):
        with pytest.raises(ValueError):
            parse_candidate(raw)

    @pytest.mark.parametrize(
        "question",
        ["What does the text say about Row?", "According to the passage, how do I scroll?", "In this section, what is X?"],
    )
    def test_rejects_questions_that_refer_to_the_source_text(self, question):
        with pytest.raises(ValueError):
            parse_candidate(valid_json(question=question))


class TestLexicalOverlap:
    def test_identical_content_words_give_one(self):
        assert lexical_overlap("flutter widgets layouts", "Flutter widgets and layouts") == 1.0

    def test_disjoint_words_give_zero(self):
        assert lexical_overlap("quantum banana", "flutter widgets layouts") == 0.0

    def test_partial_overlap_is_a_fraction(self):
        assert lexical_overlap("flutter banana", "flutter widgets") == 0.5

    def test_stopwords_are_ignored(self):
        assert lexical_overlap("how do I flutter", "flutter") == 1.0

    def test_empty_question_gives_zero(self):
        assert lexical_overlap("", "flutter") == 0.0


class TestGenerateCandidates:
    def test_builds_rows_with_ids_and_source_fields(self):
        chunks = [make_chunk(url=f"https://docs.flutter.dev/ui/p{i}") for i in range(3)]
        rows = generate_candidates(chunks, lambda prompt: valid_json(), n=2)
        assert [r.id for r in rows] == ["c001", "c002"]
        assert rows[0].url == "https://docs.flutter.dev/ui/p0"
        assert rows[0].chunk_text == LONG_TEXT
        assert 0.0 <= rows[0].overlap <= 1.0

    def test_retries_once_on_invalid_output(self):
        replies = iter(["garbage", valid_json()])
        rows = generate_candidates([make_chunk()], lambda prompt: next(replies), n=1)
        assert len(rows) == 1

    def test_skips_chunk_after_two_failures_and_moves_on(self):
        chunks = [make_chunk(url="https://docs.flutter.dev/ui/bad"), make_chunk(url="https://docs.flutter.dev/ui/good")]
        replies = iter(["garbage", "garbage", valid_json()])
        rows = generate_candidates(chunks, lambda prompt: next(replies), n=1)
        assert [r.url for r in rows] == ["https://docs.flutter.dev/ui/good"]

    def test_stops_after_n_successes(self):
        calls = []
        chunks = [make_chunk(url=f"https://docs.flutter.dev/ui/p{i}") for i in range(5)]

        def llm(prompt):
            calls.append(prompt)
            return valid_json()

        generate_candidates(chunks, llm, n=2)
        assert len(calls) == 2
