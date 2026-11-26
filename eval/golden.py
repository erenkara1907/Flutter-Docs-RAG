"""Golden question set: row schema, loader, and whole-set consistency checks."""

from collections import Counter
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

DEFAULT_GOLDEN_PATH = Path("eval/golden.jsonl")
EXPECTED_COUNTS = {"single": 40, "multi": 15, "out_of_scope": 15, "tr": 10}
MIN_MULTI_URLS = 2


class GoldenQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    category: Literal["single", "multi", "out_of_scope", "tr"]
    lang: Literal["en", "tr"]
    question: str
    expected_urls: list[str]
    reference_answer: str
    answerable: bool

    @field_validator("question", "reference_answer")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value

    @model_validator(mode="after")
    def _category_rules(self) -> Self:
        if (self.category == "tr") != (self.lang == "tr"):
            raise ValueError("lang must be 'tr' exactly when category is 'tr'")
        if len(set(self.expected_urls)) != len(self.expected_urls):
            raise ValueError("expected_urls contains duplicates")

        if self.category == "out_of_scope":
            if self.expected_urls or self.answerable:
                raise ValueError("out_of_scope needs empty expected_urls and answerable=false")
            return self

        if not self.answerable:
            raise ValueError(f"{self.category} questions must be answerable")
        n_urls = len(self.expected_urls)
        valid_count = n_urls >= MIN_MULTI_URLS if self.category == "multi" else n_urls == 1
        if not valid_count:
            raise ValueError(f"{self.category} has wrong number of expected_urls: {n_urls}")
        return self


def load_golden(path: Path = DEFAULT_GOLDEN_PATH) -> list[GoldenQuestion]:
    with Path(path).open(encoding="utf-8") as f:
        return [GoldenQuestion.model_validate_json(line) for line in f if line.strip()]


def validate_golden(questions: list[GoldenQuestion], known_urls: set[str]) -> None:
    """Raise ValueError listing every problem found in the set as a whole."""
    problems: list[str] = []

    ids = Counter(q.id for q in questions)
    duplicates = sorted(i for i, n in ids.items() if n > 1)
    if duplicates:
        problems.append(f"duplicate ids: {duplicates}")

    for q in questions:
        problems.extend(f"{q.id}: unknown URL {url}" for url in q.expected_urls if url not in known_urls)

    counts = Counter(q.category for q in questions)
    for category, expected in EXPECTED_COUNTS.items():
        if counts[category] != expected:
            problems.append(f"category {category}: expected {expected}, got {counts[category]}")

    if problems:
        raise ValueError("\n".join(problems))
