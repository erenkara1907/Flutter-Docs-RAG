"""LLM helpers shared by rewrite, rerank, answer generation and the judge.

An LLM is just `Callable[[str], str]` (prompt in, text out), so tests pass a fake
and the same code runs on local Ollama (development) or Groq (measurements, production).

Groq's free tier is tight (8000 tokens per minute, 1000 requests per day per model), so the
Groq client waits BEFORE it would exceed the minute budget, using the rate-limit headers the
API returns, and stops at once when a per-day limit is hit. The key comes from the environment
(GROQ_API_KEY, loaded from .env) and is never logged.
"""

import json
import logging
import os
import re
import time
from collections.abc import Callable, Iterator
from typing import Literal

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/v1"
OLLAMA_MODEL = "llama3.2"
GROQ_URL = "https://api.groq.com/openai/v1"
GROQ_KEY_VARIABLE = "GROQ_API_KEY"

Role = Literal["rewrite", "rerank", "answer", "judge"]
Provider = Literal["ollama", "groq"]

# Llama models were removed from this account's catalog, so the judge is Qwen: a different
# model family from the answerer (a model tends to rate its own answers too high).
GROQ_MODELS: dict[str, str] = {
    "rewrite": "openai/gpt-oss-20b",
    "rerank": "openai/gpt-oss-20b",
    "answer": "openai/gpt-oss-120b",
    "judge": "qwen/qwen3.8-27b",
}
_MAX_TOKENS = {"rewrite": 600, "rerank": 800, "answer": 1500, "judge": 1000}
_REASONING_EFFORT = {"rewrite": "low", "rerank": "low", "answer": "medium"}  # gpt-oss only

MAX_RETRIES = 5
DEFAULT_RETRY_WAIT_S = 20.0
WAIT_MARGIN_S = 0.5
CHARS_PER_TOKEN = 3  # rough; prompts mix English and code

Llm = Callable[[str], str]
LlmStream = Callable[[str], Iterator[str]]

_FENCE_WRAPPER = re.compile(r"^```(?:json)?\s*|\s*```$")
_DURATION_PART = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
_UNIT_SECONDS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}
_TRY_AGAIN = re.compile(r"try again in ([0-9hms.]+)", re.IGNORECASE)


class DailyQuotaExceeded(RuntimeError):
    """Waiting will not help: a per-day limit resets in hours."""


def parse_json_object(raw: str) -> dict:
    """Parse a model reply that should be one JSON object. Raises ValueError otherwise."""
    data = json.loads(_FENCE_WRAPPER.sub("", raw.strip()))
    if not isinstance(data, dict):
        raise ValueError("reply is not a JSON object")
    return data


def parse_duration(text: str | None) -> float | None:
    """'1m30.5s' -> 90.5, '250ms' -> 0.25. None when there is nothing to read."""
    parts = _DURATION_PART.findall(text or "")
    if not parts:
        return None
    return sum(float(number) * _UNIT_SECONDS[unit] for number, unit in parts)


def seconds_to_wait(remaining_tokens: int | None, reset_s: float | None, needed: int) -> float:
    """How long to sleep before a request needing `needed` tokens, given the last known quota."""
    if remaining_tokens is None or remaining_tokens >= needed:
        return 0.0
    return (60.0 if reset_s is None else reset_s) + WAIT_MARGIN_S


def estimate_tokens(prompt: str, max_tokens: int) -> int:
    """Groq counts the prompt plus the requested output against the minute budget."""
    return len(prompt) // CHARS_PER_TOKEN + max_tokens


def is_daily_quota(message: str) -> bool:
    return "per day" in message.lower()


def retry_wait(message: str) -> float:
    """Seconds to wait after a 429, read from 'Please try again in 7.66s' (else a default)."""
    hint = _TRY_AGAIN.search(message)
    seconds = parse_duration(hint.group(1)) if hint else None
    return DEFAULT_RETRY_WAIT_S if seconds is None else seconds + WAIT_MARGIN_S


def ollama_llm(model: str = OLLAMA_MODEL, temperature: float = 0.0, seed: int | None = None) -> Llm:
    client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")  # key is ignored by Ollama
    extra = {} if seed is None else {"seed": seed}

    def call(prompt: str) -> str:
        reply = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=temperature,
            **extra,
        )
        return reply.choices[0].message.content or ""

    return call


def _groq_client() -> OpenAI:
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get(GROQ_KEY_VARIABLE)
    if not api_key:
        raise RuntimeError(f"{GROQ_KEY_VARIABLE} is not set; put it in .env")
    return OpenAI(base_url=GROQ_URL, api_key=api_key, max_retries=0)


def _chat_options(
    temperature: float, max_tokens: int, seed: int | None, reasoning_effort: str | None, json_mode: bool = True
) -> dict:
    options: dict = {"temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        options["response_format"] = {"type": "json_object"}
    if seed is not None:
        options["seed"] = seed
    if reasoning_effort is not None:
        options["extra_body"] = {"reasoning_effort": reasoning_effort}
    return options


def groq_stream(
    model: str,
    temperature: float = 0.0,
    seed: int | None = None,
    max_tokens: int = 1500,
    reasoning_effort: str | None = None,
    client: OpenAI | None = None,
) -> LlmStream:
    """Like groq_llm, but yields the reply piece by piece. It never waits for quota: a person is watching.

    JSON mode is off: with it Groq sends the whole reply in one piece. The prompt still demands JSON,
    and the caller validates the finished reply exactly as for a non-streamed one.
    """
    groq = client if client is not None else _groq_client()
    options = _chat_options(temperature, max_tokens, seed, reasoning_effort, json_mode=False)

    def stream(prompt: str) -> Iterator[str]:
        try:
            response = groq.chat.completions.create(
                model=model, messages=[{"role": "user", "content": prompt}], stream=True, **options
            )
            for part in response:
                if part.choices and part.choices[0].delta.content:
                    yield part.choices[0].delta.content
        except openai.RateLimitError as error:
            if is_daily_quota(str(error)):
                raise DailyQuotaExceeded(f"Groq daily quota for {model} is used up") from None
            raise

    return stream


def groq_llm(
    model: str,
    temperature: float = 0.0,
    seed: int | None = None,
    max_tokens: int = 1000,
    reasoning_effort: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
    on_wait: Callable[[float], None] | None = None,
) -> Llm:
    """`on_wait` is told about every pause, so callers can keep quota waits out of latency numbers."""
    client = _groq_client()  # its own retries are off: they are handled below
    options = _chat_options(temperature, max_tokens, seed, reasoning_effort)

    quota = {"remaining": None, "reset_at": 0.0}  # last known minute budget

    def rest(seconds: float) -> None:
        if on_wait is not None:
            on_wait(seconds)
        sleep(seconds)

    def wait_for_budget(prompt: str) -> None:
        reset_in = max(0.0, quota["reset_at"] - clock())
        pause = seconds_to_wait(quota["remaining"], reset_in, estimate_tokens(prompt, max_tokens))
        if pause > 0:
            logger.info("waiting %.0fs for the Groq token budget (%s)", pause, model)
            rest(pause)
            quota["remaining"] = None

    def remember_budget(headers) -> None:
        remaining = headers.get("x-ratelimit-remaining-tokens")
        reset_s = parse_duration(headers.get("x-ratelimit-reset-tokens"))
        quota["remaining"] = int(remaining) if remaining is not None else None
        quota["reset_at"] = clock() + (reset_s if reset_s is not None else 60.0)

    def call(prompt: str) -> str:
        wait_for_budget(prompt)
        messages = [{"role": "user", "content": prompt}]
        for attempt in range(MAX_RETRIES + 1):
            try:
                raw = client.chat.completions.with_raw_response.create(model=model, messages=messages, **options)
            except openai.RateLimitError as error:
                message = str(error)
                if is_daily_quota(message):
                    raise DailyQuotaExceeded(
                        f"Groq daily quota for {model} is used up. Finished work is kept: "
                        "resume after the quota resets (about 24 hours)."
                    ) from None
                if attempt == MAX_RETRIES:
                    raise
                pause = retry_wait(message)
                logger.warning("Groq 429 on %s, retry %d/%d in %.0fs", model, attempt + 1, MAX_RETRIES, pause)
                rest(pause)
                continue
            remember_budget(raw.headers)
            return raw.parse().choices[0].message.content or ""
        raise AssertionError("unreachable")

    return call


def make_llm_stream(role: Role, seed: int | None = None) -> LlmStream:
    """Streaming Groq model for one job (used by the live site)."""
    return groq_stream(
        GROQ_MODELS[role], seed=seed, max_tokens=_MAX_TOKENS[role], reasoning_effort=_REASONING_EFFORT.get(role)
    )


def make_llm(
    role: Role,
    provider: Provider = "ollama",
    seed: int | None = None,
    on_wait: Callable[[float], None] | None = None,
) -> Llm:
    """The model for one job. Ollama (local llama3.2) for development, Groq for measurements."""
    if provider == "ollama":
        return ollama_llm(temperature=0.0, seed=seed)
    return groq_llm(
        GROQ_MODELS[role],
        seed=seed,
        max_tokens=_MAX_TOKENS[role],
        reasoning_effort=_REASONING_EFFORT.get(role),
        on_wait=on_wait,
    )
