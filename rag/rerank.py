"""LLM rerank: from N retrieved candidates, ask a model which few are best.

The model only returns passage NUMBERS. The code maps them back to the real chunks,
so the model cannot invent a source or a URL.
"""

import logging

from rag.llm import Llm, parse_json_object
from rag.retrieve import Hit

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2
MAX_CHUNK_CHARS = 400  # keeps 20 candidates inside a small local model's context window

_PROMPT = """You rank search results for a Flutter documentation search engine.
Below are a developer's question and __N__ numbered passages. Choose the __TOP_K__ passages most likely to contain the answer, best first.

Reply with JSON only, using the passage numbers: {"ranking": [3, 1, 2]}
Give at most __TOP_K__ numbers. Do not repeat a number.

Question: __QUESTION__

Passages:
__PASSAGES__"""


def _label(hit: Hit) -> str:
    chunk = hit.chunk
    return f"{chunk.title} > {chunk.heading}" if chunk.heading else chunk.title


def build_prompt(question: str, hits: list[Hit], top_k: int) -> str:
    passages = "\n\n".join(
        f"[{number}] {_label(hit)}\n{hit.chunk.text[:MAX_CHUNK_CHARS]}" for number, hit in enumerate(hits, start=1)
    )
    return (
        _PROMPT.replace("__N__", str(len(hits)))
        .replace("__TOP_K__", str(top_k))
        .replace("__QUESTION__", question)
        .replace("__PASSAGES__", passages)
    )


def parse_ranking(raw: str, n_candidates: int, top_k: int) -> list[int]:
    """Zero-based candidate indices, best first. Invalid or repeated numbers are dropped.

    Raises ValueError when nothing usable is left.
    """
    ranking = parse_json_object(raw).get("ranking")
    if not isinstance(ranking, list):
        raise ValueError("'ranking' must be a list")

    indices: list[int] = []
    for number in ranking:
        is_valid = type(number) is int and 1 <= number <= n_candidates and number - 1 not in indices
        if is_valid:
            indices.append(number - 1)
    if not indices:
        raise ValueError("ranking has no valid passage numbers")
    return indices[:top_k]


def rerank(question: str, hits: list[Hit], llm: Llm, top_k: int, attempts: int = MAX_ATTEMPTS) -> list[Hit]:
    """Best `top_k` hits. Slots the model leaves empty are filled in the original order;
    if every attempt fails the original order is kept."""
    if not hits:
        return []
    prompt = build_prompt(question, hits, top_k)
    for attempt in range(1, attempts + 1):
        try:
            chosen = parse_ranking(llm(prompt), len(hits), top_k)
        except ValueError as error:
            logger.warning("rerank attempt %d/%d failed: %s", attempt, attempts, error)
            continue
        rest = [i for i in range(len(hits)) if i not in chosen]
        return [hits[i] for i in (chosen + rest)[:top_k]]
    return hits[:top_k]
