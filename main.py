"""The web API: POST /api/ask. Run locally with `uv run uvicorn main:app`.

The live site searches by keywords only (config r7: BM25 + query rewrite), so the server needs
no embedding model. Models and the index are loaded on the first question, not at import time.
"""

import json
import logging
import os
import threading
import time
from collections import deque
from collections.abc import Callable, Iterator, Mapping
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from rag.answer import Answer, answer_question, validate_question
from rag.config import load_config
from rag.llm import DailyQuotaExceeded, Llm, LlmStream, make_llm, make_llm_stream
from rag.pipeline import LLM_SEED, Searcher, make_searcher
from rag.stream import stream_answer

logger = logging.getLogger(__name__)

LIVE_CONFIG = "r7"
RATE_LIMIT = 10  # questions per client per window
RATE_WINDOW_SECONDS = 60.0
BUSY_MESSAGE = "Servis şu an yoğun veya kullanılamıyor. Biraz sonra tekrar dene."
RATE_LIMIT_MESSAGE = "Çok fazla soru sordun. Bir dakika sonra tekrar dene."

AnswerFn = Callable[[str], Answer]
StreamFn = Callable[[str], Iterator[dict]]


class AskRequest(BaseModel):
    question: str


class SlidingWindowLimiter:
    """At most `limit` calls per client in the last `window` seconds. In memory, so best effort on serverless."""

    def __init__(self, limit: int, window: float, clock: Callable[[], float] = time.monotonic) -> None:
        self._limit = limit
        self._window = window
        self._clock = clock
        self._calls: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, client: str) -> bool:
        now = self._clock()
        with self._lock:
            self._forget_idle(now)
            calls = self._calls.setdefault(client, deque())
            if len(calls) >= self._limit:
                return False
            calls.append(now)
            return True

    def known_clients(self) -> set[str]:
        with self._lock:
            return set(self._calls)

    def _forget_idle(self, now: float) -> None:
        cutoff = now - self._window
        for client in list(self._calls):
            calls = self._calls[client]
            while calls and calls[0] <= cutoff:
                calls.popleft()
            if not calls:
                del self._calls[client]


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _checked_question(body: AskRequest, request: Request, limiter: SlidingWindowLimiter) -> str:
    """Rate limit first (so rejected questions count too), then validate. Raises HTTPException."""
    if not limiter.allow(_client_key(request)):
        raise HTTPException(status_code=429, detail=RATE_LIMIT_MESSAGE)
    try:
        return validate_question(body.question)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from None


def _ndjson(events: Iterator[dict]) -> Iterator[str]:
    """One JSON event per line. A failure becomes an error event: the status line was already sent."""
    try:
        for event in events:
            yield json.dumps(event, ensure_ascii=False) + "\n"
    except DailyQuotaExceeded:
        logger.warning("model quota exhausted")
        yield json.dumps({"type": "error", "message": BUSY_MESSAGE}) + "\n"
    except Exception:
        logger.exception("streaming failed")
        yield json.dumps({"type": "error", "message": BUSY_MESSAGE}) + "\n"


def create_app(answer_fn: AnswerFn, limiter: SlidingWindowLimiter, stream_fn: StreamFn | None = None) -> FastAPI:
    app = FastAPI(title="flutter-docs-rag", docs_url=None, redoc_url=None, openapi_url=None)

    @app.post("/api/ask", response_model=Answer)
    def ask(body: AskRequest, request: Request) -> Answer:
        question = _checked_question(body, request, limiter)
        try:
            return answer_fn(question)
        except DailyQuotaExceeded:
            logger.warning("model quota exhausted")
            raise HTTPException(status_code=503, detail=BUSY_MESSAGE) from None
        except Exception:
            logger.exception("answering failed")
            raise HTTPException(status_code=503, detail=BUSY_MESSAGE) from None

    if stream_fn is not None:

        @app.post("/api/ask/stream")
        def ask_stream(body: AskRequest, request: Request) -> StreamingResponse:
            question = _checked_question(body, request, limiter)
            return StreamingResponse(
                _ndjson(stream_fn(question)),
                media_type="application/x-ndjson",
                headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
            )

    return app


@lru_cache(maxsize=1)
def _live_parts() -> tuple[Searcher, Llm, LlmStream]:
    load_dotenv()  # local development only; on the server the keys are real environment variables
    searcher = make_searcher(load_config(LIVE_CONFIG), make_llm("rewrite", "groq", LLM_SEED))
    return searcher, make_llm("answer", "groq", LLM_SEED), make_llm_stream("answer", LLM_SEED)


def live_answer(question: str) -> Answer:
    searcher, llm, _ = _live_parts()
    return answer_question(question, searcher, llm)


def live_stream(question: str) -> Iterator[dict]:
    searcher, _, stream_llm = _live_parts()
    return stream_answer(question, searcher, stream_llm)


app = create_app(live_answer, SlidingWindowLimiter(RATE_LIMIT, RATE_WINDOW_SECONDS), live_stream)


def should_serve_static(environ: Mapping[str, str]) -> bool:
    """On Vercel the CDN serves public/ itself and the docs say not to mount it; locally we do."""
    return "VERCEL" not in environ


if should_serve_static(os.environ) and Path("public").is_dir():  # mounted last, so /api/ask wins
    app.mount("/", StaticFiles(directory="public", html=True), name="public")
