"""Streaming answers: the model writes one JSON object, and the text of its "answer" field is shown as it arrives.

Events (plain dicts, one per line on the wire):
    {"type": "meta",  "search_query": "..."}   what was searched, sent before the first token
    {"type": "token", "text": "..."}           next piece of the answer text
    {"type": "reset"}                          the reply was rejected; clear the text, a retry follows
    {"type": "done",  "answer": {...}}         the checked Answer: the only thing to trust

Tokens are a preview. Sources and the final status come only from `done`, after the whole reply
has been validated exactly like the non-streaming path.
"""

import json
import logging
import re
from collections.abc import Iterator

from rag.answer import (
    MAX_ATTEMPTS,
    NOT_FOUND_MESSAGE,
    Answer,
    build_prompt,
    invalid_reply_answer,
    reply_to_answer,
    validate_question,
)
from rag.llm import LlmStream
from rag.pipeline import Searcher

logger = logging.getLogger(__name__)

_ANSWER_START = re.compile(r'"answer"\s*:\s*"')
_HIGH_SURROGATES = range(0xD800, 0xDC00)
_UNICODE_ESCAPE_LENGTH = 6  # \uXXXX


class AnswerExtractor:
    """Pulls the decoded text of the "answer" string out of a JSON reply that arrives in arbitrary pieces."""

    def __init__(self) -> None:
        self._buffer = ""
        self._in_answer = False
        self._finished = False

    def feed(self, piece: str) -> str:
        """Returns the answer text that became available with this piece ("" if none)."""
        if self._finished:
            return ""
        self._buffer += piece
        if not self._in_answer:
            match = _ANSWER_START.search(self._buffer)
            if not match:
                return ""
            self._buffer = self._buffer[match.end() :]
            self._in_answer = True

        end, closed = _complete_prefix(self._buffer)
        segment, self._buffer = self._buffer[:end], self._buffer[end:]
        self._finished = closed
        try:
            return json.loads(f'"{segment}"', strict=False)
        except json.JSONDecodeError:
            self._finished = True  # malformed: stop previewing, the final validation will reject the reply
            return ""


def _complete_prefix(text: str) -> tuple[int, bool]:
    """How much of `text` (the inside of a JSON string) can be decoded now, and whether the string has closed.

    Never cuts inside an escape sequence or between the two halves of a surrogate pair.
    """
    i = 0
    while i < len(text):
        char = text[i]
        if char == '"':
            return i, True
        if char != "\\":
            i += 1
            continue
        if i + 1 >= len(text):
            break
        if text[i + 1] != "u":
            i += 2
            continue
        if i + _UNICODE_ESCAPE_LENGTH > len(text):
            break
        try:
            code = int(text[i + 2 : i + _UNICODE_ESCAPE_LENGTH], 16)
        except ValueError:
            return i, True  # not a valid escape: treat as the end and let validation reject the reply
        width = _UNICODE_ESCAPE_LENGTH * 2 if code in _HIGH_SURROGATES else _UNICODE_ESCAPE_LENGTH
        if i + width > len(text):
            break
        i += width
    return i, False


def _done(answer: Answer, search_query: str | None) -> dict:
    final = answer.model_copy(update={"search_query": search_query})
    return {"type": "done", "answer": final.model_dump()}


def stream_answer(question: str, searcher: Searcher, stream_llm: LlmStream, attempts: int = MAX_ATTEMPTS) -> Iterator[dict]:
    """Search, then stream the answer. Raises ValueError for an empty or too long question."""
    cleaned = validate_question(question)
    result = searcher(cleaned)
    yield {"type": "meta", "search_query": result.search_query}

    if not result.is_flutter_question or not result.hits:
        yield _done(Answer(answer=NOT_FOUND_MESSAGE, status="not_found"), result.search_query)
        return

    prompt = build_prompt(cleaned, result.hits)
    for attempt in range(1, attempts + 1):
        raw, extractor, previewed = "", AnswerExtractor(), False
        for piece in stream_llm(prompt):
            raw += piece
            text = extractor.feed(piece)
            if text:
                previewed = True
                yield {"type": "token", "text": text}
        try:
            yield _done(reply_to_answer(raw, result.hits), result.search_query)
            return
        except ValueError as error:
            logger.warning("streamed answer attempt %d/%d rejected: %s", attempt, attempts, error)
            if previewed:
                yield {"type": "reset"}
    yield _done(invalid_reply_answer(result.hits), result.search_query)
