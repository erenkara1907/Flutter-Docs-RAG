"""Stage 2 of the evaluation: search, answer and judge every golden question.

Code computes source accuracy, refusal accuracy, latency and model-call counts;
the judge model scores accuracy and faithfulness. Progress is saved after every
question, so a quota stop or a crash resumes where it left off.
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from eval.golden import GoldenQuestion, load_golden
from eval.judge import judge_answer
from eval.metrics import unique_urls
from rag.answer import Answer, answer_question
from rag.config import RunConfig
from rag.llm import GROQ_MODELS, OLLAMA_MODEL, Llm, Provider, make_llm
from rag.pipeline import LLM_SEED, SearchResult, Searcher, make_searcher

logger = logging.getLogger(__name__)

PROGRESS_DIR = Path("data/cache/eval")
_RETRIEVAL_PREFIXES = ("hit@", "recall@", "ndcg@")


@dataclass
class CallCounter:
    """Counts model calls and the seconds spent waiting for a rate limit (not real latency)."""

    calls: int = 0
    waited_s: float = 0.0

    def add_wait(self, seconds: float) -> None:
        self.waited_s += seconds


def counted(llm: Llm, counter: CallCounter) -> Llm:
    def call(prompt: str) -> str:
        counter.calls += 1
        return llm(prompt)

    return call


class ProgressStore:
    """One JSON line per finished question."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def load(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        with self._path.open(encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return {row["id"]: row for row in rows}

    def append(self, row: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def clear(self) -> None:
        self._path.unlink(missing_ok=True)


def source_correct(answer: Answer, question: GoldenQuestion) -> bool | None:
    """Did a cited page match an expected page? Undefined when nothing was answered."""
    if answer.status != "answered" or not question.expected_urls:
        return None
    return bool({s.url for s in answer.sources} & set(question.expected_urls))


def refusal_correct(answer: Answer, question: GoldenQuestion) -> bool:
    """Answerable questions should be answered; out-of-scope ones should get 'not found'."""
    if question.answerable:
        return answer.status == "answered"
    return answer.status == "not_found"


def _retrieval_scores(question: GoldenQuestion, result: SearchResult, k: int) -> dict[str, float]:
    if not question.expected_urls:
        return {}
    from eval.run import score_question  # imported here: eval.run imports this module lazily too

    return score_question(question, [hit.chunk.url for hit in result.hits], k)


def run_question(
    question: GoldenQuestion,
    searcher: Searcher,
    answer_llm: Llm,
    judge_llm: Llm,
    counter: CallCounter,
    k: int,
    clock: Callable[[], float],
) -> dict:
    seen: dict[str, SearchResult] = {}

    def recording(text: str) -> SearchResult:
        seen["result"] = searcher(text)
        return seen["result"]

    calls_before, waited_before = counter.calls, counter.waited_s
    started = clock()
    answer = answer_question(question.question, recording, answer_llm)
    elapsed = clock() - started
    latency_ms = round((elapsed - (counter.waited_s - waited_before)) * 1000, 1)
    result = seen["result"]

    row = {
        "id": question.id,
        "category": question.category,
        "lang": question.lang,
        "question": question.question,
        "answerable": question.answerable,
        "search_query": answer.search_query,
        "status": answer.status,
        "answer": answer.answer,
        "sources": [s.url for s in answer.sources],
        "retrieved_urls": unique_urls([hit.chunk.url for hit in result.hits]),
        "expected_urls": question.expected_urls,
        "refusal_correct": refusal_correct(answer, question),
        "source_correct": source_correct(answer, question),
        **_retrieval_scores(question, result, k),
        "latency_ms": latency_ms,
        "llm_calls": counter.calls - calls_before,
        "judged": False,
        "accuracy": None,
        "faithfulness": None,
        "judge_reasoning": None,
    }
    if answer.status == "answered" and question.answerable:
        passages = [hit.chunk.text for hit in result.hits]
        score = judge_answer(question.question, question.reference_answer, answer.answer, passages, judge_llm)
        if score is not None:
            row = {
                **row,
                "judged": True,
                "accuracy": score.accuracy,
                "faithfulness": score.faithfulness,
                "judge_reasoning": score.reasoning,
            }
    return row


def run_full(
    questions: list[GoldenQuestion],
    searcher: Searcher,
    answer_llm: Llm,
    judge_llm: Llm,
    counter: CallCounter,
    store: ProgressStore,
    k: int = 5,
    clock: Callable[[], float] = time.perf_counter,
) -> list[dict]:
    done = store.load()
    rows = []
    for number, question in enumerate(questions, start=1):
        row = done.get(question.id)
        if row is None:
            row = run_question(question, searcher, answer_llm, judge_llm, counter, k, clock)
            store.append(row)
            logger.info("%d/%d %s %s accuracy=%s", number, len(questions), question.id, row["status"], row["accuracy"])
        rows.append(row)
    return rows


def run_stage_full(config: RunConfig, provider: Provider, fresh: bool = False) -> dict:
    """Wire real models and run the whole golden set. Rewrite/rerank, answer and judge are three roles."""
    counter = CallCounter()
    needs_search_llm = config.rewrite or config.rerank
    search_llm = counted(make_llm("rewrite", provider, LLM_SEED, counter.add_wait), counter) if needs_search_llm else None
    answer_llm = counted(make_llm("answer", provider, LLM_SEED, counter.add_wait), counter)
    judge_llm = make_llm("judge", provider, LLM_SEED)  # not counted: it is part of the evaluation, not the system

    store = ProgressStore(PROGRESS_DIR / f"{config.name}-full-{provider}.jsonl")
    if fresh:
        store.clear()
    rows = run_full(load_golden(), make_searcher(config, search_llm), answer_llm, judge_llm, counter, store, config.top_k)
    return build_report(rows, config.name, provider, config.top_k)


def log_summary(report: dict) -> None:
    def show(name: str, summary: dict) -> str:
        def fmt(value: float | None) -> str:
            return "n/a" if value is None else f"{value:.3f}"

        return (
            f"{name:<13} n={summary['n']:<3} judged={summary['n_judged']:<3} acc={fmt(summary['accuracy'])} "
            f"faith={fmt(summary['faithfulness'])} src={fmt(summary['source_accuracy'])} "
            f"refusal={fmt(summary['refusal_accuracy'])} ms={fmt(summary['mean_latency_ms'])} "
            f"calls={fmt(summary['mean_llm_calls'])}"
        )

    logger.info(show("overall", report["overall"]))
    for name, summary in report["by_category"].items():
        logger.info(show(name, summary))
    for name, summary in report["by_lang"].items():
        logger.info(show(f"lang:{name}", summary))
    logger.info("retrieval: %s", {key: round(value, 3) for key, value in report["retrieval"].items()})


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _rate(flags: list[bool]) -> float | None:
    return _mean([float(flag) for flag in flags])


def summarize_rows(rows: list[dict]) -> dict:
    """Averages that cannot be computed are None, never a misleading 0."""
    judged = [row for row in rows if row["judged"]]
    answerable = [row for row in rows if row["answerable"]]
    out_of_scope = [row for row in rows if not row["answerable"]]
    return {
        "n": len(rows),
        "n_judged": len(judged),
        "n_invalid_reply": sum(row["status"] == "invalid_reply" for row in rows),
        "accuracy": _mean([row["accuracy"] for row in judged]),
        "faithfulness": _mean([row["faithfulness"] for row in judged]),
        "source_accuracy": _rate([row["source_correct"] for row in rows if row["source_correct"] is not None]),
        "refusal_accuracy": _rate([row["refusal_correct"] for row in rows]),
        "answered_rate": _rate([row["status"] == "answered" for row in answerable]),
        "out_of_scope_refused_rate": _rate([row["status"] == "not_found" for row in out_of_scope]),
        "mean_latency_ms": _mean([row["latency_ms"] for row in rows]),
        "mean_llm_calls": _mean([row["llm_calls"] for row in rows]),
    }


def _group(rows: list[dict], key: str) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)
    return {name: summarize_rows(group) for name, group in sorted(groups.items())}


def build_report(rows: list[dict], config_name: str, provider: Provider, k: int) -> dict:
    retrieval_keys = sorted({key for row in rows for key in row if key.startswith(_RETRIEVAL_PREFIXES) or key == "mrr"})
    models = {role: (OLLAMA_MODEL if provider == "ollama" else model) for role, model in GROQ_MODELS.items()}
    return {
        "config": config_name,
        "stage": "full",
        "provider": provider,
        "models": models,
        "k": k,
        "overall": summarize_rows(rows),
        "retrieval": {key: _mean([row[key] for row in rows if key in row]) for key in retrieval_keys},
        "by_category": _group(rows, "category"),
        "by_lang": _group(rows, "lang"),
        "per_question": rows,
    }
