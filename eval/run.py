"""Run the golden set through a retrieval config and write a metrics report.

    python -m eval.run --config r0 --stage retrieval
"""

import argparse
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from eval.golden import DEFAULT_GOLDEN_PATH, GoldenQuestion, load_golden
from eval.metrics import hit_at_k, ndcg_at_k, recall_at_k, reciprocal_rank, unique_urls
from rag.config import RunConfig, load_config
from rag.llm import DailyQuotaExceeded, Llm, make_llm
from rag.pipeline import LLM_SEED, make_searcher
from rag.retrieve import DEFAULT_TOP_K

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("eval/results")

@dataclass(frozen=True)
class Retrieval:
    urls: list[str]  # URLs of the retrieved chunks, best first (repeats allowed)
    search_query: str | None = None  # what was actually searched, when the question was rewritten


Retriever = Callable[[str], Retrieval]


def score_question(question: GoldenQuestion, retrieved_urls: list[str], k: int) -> dict[str, float]:
    ranked = unique_urls(retrieved_urls)
    expected = set(question.expected_urls)
    return {
        f"hit@{k}": hit_at_k(ranked, expected, k),
        f"recall@{k}": recall_at_k(ranked, expected, k),
        "mrr": reciprocal_rank(ranked, expected),
        f"ndcg@{k}": ndcg_at_k(ranked, expected, k),
    }


def mean_metrics(rows: list[dict]) -> dict[str, float]:
    """Average every metric present in the first row."""
    if not rows:
        return {}
    return {name: sum(row[name] for row in rows) / len(rows) for name in rows[0]}


def _summarize(rows: list[dict], metric_names: list[str]) -> dict:
    means = mean_metrics([{name: row[name] for name in metric_names} for row in rows])
    return {**means, "n": len(rows)}


def _group_by(rows: list[dict], key: str, metric_names: list[str]) -> dict[str, dict]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row[key], []).append(row)
    return {name: _summarize(group, metric_names) for name, group in sorted(groups.items())}


def evaluate(questions: list[GoldenQuestion], retriever: Retriever, k: int = DEFAULT_TOP_K) -> dict:
    scorable = [q for q in questions if q.expected_urls]
    if not scorable:
        raise ValueError("no scorable questions (all have empty expected_urls)")

    rows = []
    for question in scorable:
        started = time.perf_counter()
        retrieved = retriever(question.question)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        rewritten = {} if retrieved.search_query is None else {"search_query": retrieved.search_query}
        rows.append(
            {
                "id": question.id,
                "category": question.category,
                "lang": question.lang,
                "question": question.question,
                **rewritten,
                "expected_urls": question.expected_urls,
                "retrieved_urls": unique_urls(retrieved.urls),
                **score_question(question, retrieved.urls, k),
                "latency_ms": latency_ms,
            }
        )

    metric_names = list(score_question(scorable[0], [], k))
    return {
        "k": k,
        "n_scored": len(rows),
        "n_skipped_out_of_scope": len(questions) - len(scorable),
        "mean_latency_ms": round(sum(row["latency_ms"] for row in rows) / len(rows), 1),
        "overall": _summarize(rows, metric_names),
        "by_category": _group_by(rows, "category", metric_names),
        "by_lang": _group_by(rows, "lang", metric_names),
        "per_question": rows,
    }


def write_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def retrieval_llm(config: RunConfig, provider: str) -> Llm | None:
    """Groq model for rewrite/rerank when asked for. None lets the pipeline use its local dev model."""
    if provider == "groq" and (config.rewrite or config.rerank):
        return make_llm("rewrite", provider, LLM_SEED)
    return None


def make_retriever(config: RunConfig, llm: Llm | None = None) -> Retriever:
    searcher = make_searcher(config, llm)

    def retrieve(question: str) -> Retrieval:
        result = searcher(question)
        return Retrieval(urls=[hit.chunk.url for hit in result.hits], search_query=result.search_query)

    return retrieve


def _log_summary(report: dict) -> None:
    def line(name: str, values: dict) -> str:
        metrics = "  ".join(f"{m}={v:.3f}" for m, v in values.items() if m != "n")
        return f"{name:<14} n={values['n']:<3} {metrics}"

    logger.info(line("overall", report["overall"]))
    logger.info("mean latency %.0f ms per question", report["mean_latency_ms"])
    for name, values in report["by_category"].items():
        logger.info(line(name, values))
    for name, values in report["by_lang"].items():
        logger.info(line(f"lang:{name}", values))


def run_full_stage(config: RunConfig, provider: str, fresh: bool) -> None:
    from eval.full import log_summary, run_stage_full  # lazy: eval.full imports this module

    try:
        report = run_stage_full(config, provider, fresh)
    except DailyQuotaExceeded as error:
        raise SystemExit(f"stopped: {error}") from None
    output = RESULTS_DIR / f"{config.name}-full-{provider}.json"
    write_report(report, output)
    log_summary(report)
    logger.info("wrote %s", output)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--stage", required=True, choices=["retrieval", "full"])
    parser.add_argument(
        "--provider", choices=["ollama", "groq"], default="ollama",
        help="models for --stage full, and for rewrite/rerank in --stage retrieval",
    )
    parser.add_argument("--fresh", action="store_true", help="ignore saved progress of an earlier --stage full run")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.stage == "full":
        run_full_stage(config, args.provider, args.fresh)
        return
    report = {
        "config": config.name,
        "stage": args.stage,
        **evaluate(load_golden(DEFAULT_GOLDEN_PATH), make_retriever(config, retrieval_llm(config, args.provider)), config.top_k),
    }
    output = RESULTS_DIR / f"{config.name}-{args.stage}.json"
    write_report(report, output)
    _log_summary(report)
    logger.info("wrote %s", output)


if __name__ == "__main__":
    main()
