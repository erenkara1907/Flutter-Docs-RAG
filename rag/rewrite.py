"""Query rewriting: turn any-language question into a short English documentation search query."""

import logging

from pydantic import BaseModel, ConfigDict, field_validator

from rag.llm import Llm, parse_json_object

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
MAX_QUERY_CHARS = 200

_PROMPT = """You convert a Flutter developer's question, written in any language, into a short English search query for the Flutter documentation.

Rules:
- Output 3 to 12 English words: the key concepts and the exact Flutter/Dart names involved (widgets, classes, packages, commands).
- Keep identifiers exactly as written, for example ListView, setState, pubspec.yaml.
- Do not answer the question. Do not add words that are not needed.
- is_flutter_question is false only if the question has nothing to do with Flutter, Dart or app development.

Examples:
Question: Bir butonun rengini nasıl değiştirebilirim?
{"search_query": "change button color style ElevatedButton", "is_flutter_question": true}
Question: What is the best pizza in Rome?
{"search_query": "pizza Rome", "is_flutter_question": false}

Reply with JSON only: {"search_query": "...", "is_flutter_question": true}

Question: __QUESTION__"""


class Rewrite(BaseModel):
    model_config = ConfigDict(frozen=True)

    search_query: str
    is_flutter_question: bool

    @field_validator("search_query")
    @classmethod
    def _usable_query(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("search_query must not be empty")
        if len(value) > MAX_QUERY_CHARS:
            raise ValueError(f"search_query is longer than {MAX_QUERY_CHARS} characters")
        return value


def build_prompt(question: str) -> str:
    return _PROMPT.replace("__QUESTION__", question)


def parse_rewrite(raw: str) -> Rewrite:
    """Validate a model reply. Raises ValueError for anything unusable."""
    return Rewrite.model_validate(parse_json_object(raw))


def rewrite_query(question: str, llm: Llm, attempts: int = MAX_ATTEMPTS) -> Rewrite:
    """Ask the model; on repeated bad replies search with the original question instead of failing."""
    for attempt in range(1, attempts + 1):
        try:
            return parse_rewrite(llm(build_prompt(question)))
        except ValueError as error:
            logger.warning("rewrite attempt %d/%d failed: %s", attempt, attempts, error)
    return Rewrite(search_query=question, is_flutter_question=True)
