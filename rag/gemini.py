"""Gemini embeddings: request batching, spacing between requests, retry with backoff.

The API key is read from the environment only (GEMINI_API_KEY, loaded from .env)
and is never logged or put in an error message.
"""

import logging
import os
import re
import time
from collections.abc import Callable

import numpy as np

from rag.llm import DailyQuotaExceeded, is_daily_quota

logger = logging.getLogger(__name__)

KEY_VARIABLE = "GEMINI_API_KEY"
RETRYABLE_CODES = frozenset({429, 500, 503, 504})
BATCH_SIZE = 50
TEXTS_PER_MINUTE = 90  # free tier allows 100 per minute; keep a margin
MAX_RETRIES = 6
BACKOFF_START_S = 10.0
BACKOFF_MAX_S = 120.0

_RETRY_HINT = re.compile(r"retry in ([0-9.]+)s", re.IGNORECASE)

BatchCall = Callable[[list[str]], np.ndarray]
Embedder = Callable[[list[str]], np.ndarray]


def is_retryable(error: Exception) -> bool:
    """Rate limits and transient server errors. Anything else is our bug: do not retry."""
    return getattr(error, "code", None) in RETRYABLE_CODES


def retry_delay(error: Exception, attempt: int) -> float:
    """Seconds to wait: what the server asked for ("Please retry in 57s"), else exponential backoff."""
    hint = _RETRY_HINT.search(str(error))
    if hint:
        return min(float(hint.group(1)) + 1.0, BACKOFF_MAX_S)
    return min(BACKOFF_START_S * 2**attempt, BACKOFF_MAX_S)


def _call_with_retry(call: BatchCall, batch: list[str], max_retries: int, sleep: Callable[[float], None]) -> np.ndarray:
    for attempt in range(max_retries + 1):
        try:
            return call(batch)
        except Exception as error:
            if is_retryable(error) and is_daily_quota(str(error)):
                raise DailyQuotaExceeded(
                    "Gemini free-tier daily quota is used up. Vectors already cached are kept: "
                    "resume after the quota resets (about 24 hours) or enable billing."
                ) from error
            if not is_retryable(error) or attempt == max_retries:
                raise
            delay = retry_delay(error, attempt)
            logger.warning("Gemini error %s, retry %d/%d in %.0fs", getattr(error, "code", "?"), attempt + 1, max_retries, delay)
            sleep(delay)
    raise AssertionError("unreachable")


def embed_in_batches(
    call: BatchCall,
    texts: list[str],
    batch_size: int = BATCH_SIZE,
    texts_per_minute: int = TEXTS_PER_MINUTE,
    max_retries: int = MAX_RETRIES,
    sleep: Callable[[float], None] = time.sleep,
) -> np.ndarray:
    """Send `texts` in small requests, in order, never faster than `texts_per_minute`.

    The free tier counts every text in a request toward its per-minute limit, so the
    pause after a batch is proportional to the batch size.
    """
    parts: list[np.ndarray] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors = _call_with_retry(call, batch, max_retries, sleep)
        if len(vectors) != len(batch):
            raise ValueError(f"Gemini returned {len(vectors)} vectors for {len(batch)} texts")
        parts.append(np.asarray(vectors, dtype=np.float32))
        if start + batch_size < len(texts):
            sleep(len(batch) * 60 / texts_per_minute)
    return np.vstack(parts) if parts else np.zeros((0, 0), dtype=np.float32)


def gemini_embedder(model_id: str, dimensions: int | None, task_type: str) -> Embedder:
    """`task_type` is RETRIEVAL_DOCUMENT for chunks and RETRIEVAL_QUERY for questions."""
    from dotenv import load_dotenv
    from google import genai
    from google.genai import types

    load_dotenv()
    api_key = os.environ.get(KEY_VARIABLE)
    if not api_key:
        raise RuntimeError(f"{KEY_VARIABLE} is not set; put it in .env")

    client = genai.Client(api_key=api_key)
    config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=dimensions)

    def call(batch: list[str]) -> np.ndarray:
        response = client.models.embed_content(model=model_id, contents=batch, config=config)
        return np.array([e.values for e in response.embeddings], dtype=np.float32)

    return lambda texts: embed_in_batches(call, texts)
