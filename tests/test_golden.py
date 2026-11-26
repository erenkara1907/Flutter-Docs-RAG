from pathlib import Path

import pytest
from pydantic import ValidationError

from eval.golden import GoldenQuestion, load_golden, validate_golden
from rag.ingest import DEFAULT_OUTPUT, load_pages

GOLDEN_PATH = Path("eval/golden.jsonl")
URL_A = "https://docs.flutter.dev/ui/layout"
URL_B = "https://docs.flutter.dev/cookbook/lists/long-lists"


def make_row(**overrides) -> dict:
    row = {
        "id": "q001", "category": "single", "lang": "en", "question": "How?",
        "expected_urls": [URL_A], "reference_answer": "Like this.", "answerable": True,
    }
    return {**row, **overrides}


class TestGoldenQuestionRules:
    def test_valid_single_row(self):
        assert GoldenQuestion(**make_row()).category == "single"

    def test_single_needs_exactly_one_url(self):
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(expected_urls=[URL_A, URL_B]))

    def test_multi_needs_at_least_two_urls(self):
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="multi", expected_urls=[URL_A]))
        assert GoldenQuestion(**make_row(category="multi", expected_urls=[URL_A, URL_B]))

    def test_out_of_scope_has_no_urls_and_is_not_answerable(self):
        assert GoldenQuestion(**make_row(category="out_of_scope", expected_urls=[], answerable=False))
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="out_of_scope", expected_urls=[URL_A], answerable=False))
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="out_of_scope", expected_urls=[], answerable=True))

    def test_answerable_categories_must_be_answerable(self):
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(answerable=False))

    def test_tr_category_requires_turkish_language_and_vice_versa(self):
        assert GoldenQuestion(**make_row(category="tr", lang="tr"))
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="tr", lang="en"))
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="single", lang="tr"))

    def test_unknown_category_is_rejected(self):
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(category="easy"))

    def test_blank_question_is_rejected(self):
        with pytest.raises(ValidationError):
            GoldenQuestion(**make_row(question="   "))


def make_valid_set() -> list[GoldenQuestion]:
    rows = []
    for _ in range(40):
        rows.append(make_row(id=f"q{len(rows) + 1:03d}"))
    for _ in range(15):
        rows.append(make_row(id=f"q{len(rows) + 1:03d}", category="multi", expected_urls=[URL_A, URL_B]))
    for _ in range(15):
        rows.append(make_row(id=f"q{len(rows) + 1:03d}", category="out_of_scope", expected_urls=[], answerable=False))
    for _ in range(10):
        rows.append(make_row(id=f"q{len(rows) + 1:03d}", category="tr", lang="tr"))
    return [GoldenQuestion(**r) for r in rows]


class TestValidateGolden:
    def test_correct_set_passes(self):
        validate_golden(make_valid_set(), known_urls={URL_A, URL_B})

    def test_duplicate_ids_are_reported(self):
        questions = make_valid_set()
        questions[1] = questions[0]
        with pytest.raises(ValueError, match="duplicate"):
            validate_golden(questions, known_urls={URL_A, URL_B})

    def test_unknown_url_is_reported_with_its_id(self):
        with pytest.raises(ValueError, match="q001.*docs.flutter.dev/ui/layout"):
            validate_golden(make_valid_set(), known_urls={URL_B})

    def test_wrong_category_counts_are_reported(self):
        with pytest.raises(ValueError, match="single"):
            validate_golden(make_valid_set()[1:], known_urls={URL_A, URL_B})


@pytest.mark.skipif(not DEFAULT_OUTPUT.exists(), reason="run `python -m rag.ingest` first")
class TestRealGoldenFile:
    def test_golden_file_is_valid_against_the_ingested_pages(self):
        known = {p.url for p in load_pages(DEFAULT_OUTPUT)}
        validate_golden(load_golden(GOLDEN_PATH), known_urls=known)
