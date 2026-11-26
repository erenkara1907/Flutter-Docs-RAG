"""Retrieval metrics at page-URL level. Pure functions, no I/O.

`ranked` is the list of page URLs a retriever returned, best first. Pass it
through `unique_urls` first so one page cannot occupy several slots (nDCG can
exceed 1 if the same expected URL is counted twice).
`expected` is the set of correct page URLs. It must not be empty: questions
with no expected page (out_of_scope) have no retrieval metrics.
"""

import math


def unique_urls(ranked: list[str]) -> list[str]:
    """Drop repeated URLs, keeping each one at its first (best) position."""
    return list(dict.fromkeys(ranked))


def _require_expected(expected: set[str]) -> None:
    if not expected:
        raise ValueError("expected must not be empty (out_of_scope has no retrieval metrics)")


def _found_in_top_k(ranked: list[str], expected: set[str], k: int) -> set[str]:
    return expected & set(ranked[:k])


def _gain(rank: int) -> float:
    """Score of a correct result at 1-based `rank`: 1.0, 0.63, 0.5, 0.43, ..."""
    return 1 / math.log2(rank + 1)


def hit_at_k(ranked: list[str], expected: set[str], k: int) -> float:
    """1.0 if any expected URL is within the first k results, else 0.0."""
    _require_expected(expected)
    return 1.0 if _found_in_top_k(ranked, expected, k) else 0.0


def recall_at_k(ranked: list[str], expected: set[str], k: int) -> float:
    """Fraction of expected URLs found within the first k results."""
    _require_expected(expected)
    return len(_found_in_top_k(ranked, expected, k)) / len(expected)


def reciprocal_rank(ranked: list[str], expected: set[str]) -> float:
    """1 / rank of the first expected URL (rank starts at 1), 0.0 if absent."""
    _require_expected(expected)
    for rank, url in enumerate(ranked, start=1):
        if url in expected:
            return 1 / rank
    return 0.0


def ndcg_at_k(ranked: list[str], expected: set[str], k: int) -> float:
    """Binary-relevance nDCG@k: DCG / IDCG, gain 1/log2(rank + 1)."""
    _require_expected(expected)
    dcg = sum(
        _gain(rank) for rank, url in enumerate(ranked[:k], start=1) if url in expected
    )
    ideal_hits = min(len(expected), k)
    idcg = sum(_gain(rank) for rank in range(1, ideal_hits + 1))
    return dcg / idcg
