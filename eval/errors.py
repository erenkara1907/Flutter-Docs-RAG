"""Error analysis: which questions failed, and why.

    python -m eval.errors prepare --config r4v --provider groq   # failures, deep ranks, label template
    python -m eval.errors report  --config r4v --provider groq   # count the causes, top 3 for the README

Failure = retrieval metric 0, judge accuracy 2 or less, a refused answerable question,
or an answer to an out-of-scope question. Each failure gets ONE cause from a fixed list
and a one-line reason, so causes can be counted.
"""

import argparse
import csv
import json
import logging
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from eval.metrics import unique_urls
from rag.config import load_config
from rag.llm import make_llm
from rag.pipeline import LLM_SEED, make_searcher

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("eval/results")
DEEP_K = 50  # how far down to look for the expected page
LOW_ACCURACY_MAX = 2
ANSWER_PREVIEW_CHARS = 700
TOP_CAUSES = 3
CSV_HEADER = ["id", "kinds", "suggested_cause", "cause", "reason"]

CAUSES = (
    "retrieval_ranking",  # the expected page is in the deep search, but below the top k
    "retrieval_semantic_gap",  # the expected page is not even in the deep search
    "language_gap",  # a non-English question that the English search could not match
    "multi_page_coverage",  # only some of the pages a multi-page question needs were found
    "ambiguous_golden",  # another retrieved page also answers it: the golden set is too strict
    "chunking",  # right page, but the answer sits in another fragment or was split
    "rewrite_lossy",  # the rewritten query dropped the key terms
    "model_error",  # the passages held the answer and the model misread or ignored it
    "wrong_refusal",  # the passages held the answer and the model said "not found"
    "hallucinated_answer",  # answered a question the docs do not cover
    "doc_missing",  # the docs really do not contain the answer
)


def failure_kinds(row: dict, k: int) -> list[str]:
    kinds = []
    if row["answerable"] and row.get(f"hit@{k}", 1.0) == 0:
        kinds.append("retrieval_miss")
    if row["judged"] and row["accuracy"] is not None and row["accuracy"] <= LOW_ACCURACY_MAX:
        kinds.append("low_accuracy")
    if row["answerable"] and row["status"] != "answered":
        kinds.append("refused")
    if not row["answerable"] and row["status"] == "answered":
        kinds.append("hallucinated")
    return kinds


def select_failures(rows: list[dict], k: int = 5) -> list[dict]:
    failures = []
    for row in rows:
        kinds = failure_kinds(row, k)
        if kinds:
            failures.append({**row, "kinds": kinds})
    return failures


def expected_rank(ranked_urls: list[str], expected_urls: list[str]) -> int | None:
    """1-based position of the best-placed expected page, or None."""
    for rank, url in enumerate(unique_urls(ranked_urls), start=1):
        if url in expected_urls:
            return rank
    return None


def add_deep_ranks(failures: list[dict], deep_urls: Callable[[str], list[str]]) -> list[dict]:
    """Where would the expected page have ranked in a deeper search? Returns new dicts."""
    return [
        {**f, "expected_rank": expected_rank(deep_urls(f["question"]), f["expected_urls"]) if f["expected_urls"] else None}
        for f in failures
    ]


def suggest_cause(failure: dict) -> str | None:
    """Only what the numbers settle. Causes that need reading the answer are left to the reviewer."""
    kinds = failure["kinds"]
    if "hallucinated" in kinds:
        return "hallucinated_answer"
    if "retrieval_miss" in kinds:
        if failure.get("lang") == "tr" and not failure.get("search_query"):
            return "language_gap"
        return "retrieval_semantic_gap" if failure.get("expected_rank") is None else "retrieval_ranking"
    return None


def write_label_template(path: Path, failures: list[dict], force: bool = False) -> None:
    path = Path(path)
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists and may hold your labels; pass --force to overwrite")
    lines = [",".join(CSV_HEADER)]
    lines += [f"{f['id']},{'+'.join(f['kinds'])},{suggest_cause(f) or ''},," for f in failures]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_labels(path: Path, allow_unlabeled: bool = False) -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for record in csv.DictReader(f):
            qid = (record.get("id") or "").strip()
            cause = (record.get("cause") or "").strip()
            reason = (record.get("reason") or "").strip()
            if qid in labels:
                raise ValueError(f"duplicate id {qid}")
            if allow_unlabeled and not cause and not reason:
                continue
            if cause not in CAUSES:
                raise ValueError(f"{qid}: cause must be one of {', '.join(CAUSES)}; got {cause!r}")
            if not reason:
                raise ValueError(f"{qid}: reason is empty")
            labels[qid] = {"cause": cause, "reason": reason}
    return labels


def summarize_causes(failures: list[dict], labels: dict[str, dict[str, str]]) -> dict:
    failure_ids = [f["id"] for f in failures]
    for qid in labels:
        if qid not in failure_ids:
            raise ValueError(f"label for {qid}, which is not among the failures")

    labelled = [qid for qid in failure_ids if qid in labels]
    counts = Counter(labels[qid]["cause"] for qid in labelled)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return {
        "n_failures": len(failure_ids),
        "counts": dict(ordered),
        "top3": [
            {"cause": cause, "count": count, "ids": [q for q in labelled if labels[q]["cause"] == cause]}
            for cause, count in ordered[:TOP_CAUSES]
        ],
        "unlabeled": [qid for qid in failure_ids if qid not in labels],
    }


def build_dossier(failures: list[dict]) -> str:
    parts = ["# Hata analizi: başarısız sorular\n"]
    for f in failures:
        rank = f.get("expected_rank")
        deep = f"{rank}. sırada" if rank else f"ilk {DEEP_K} içinde yok"
        retrieved = "\n".join(f"  {i}. {url}" for i, url in enumerate(f["retrieved_urls"], start=1))
        answer = f["answer"][:ANSWER_PREVIEW_CHARS] + (" ..." if len(f["answer"]) > ANSWER_PREVIEW_CHARS else "")
        parts.append(
            f"## {f['id']} ({f['category']}, {f['lang']}) {' + '.join(f['kinds'])}\n\n"
            f"- **Soru:** {f['question']}\n"
            f"- **Aranan sorgu:** {f.get('search_query') or '(soru olduğu gibi)'}\n"
            f"- **Beklenen sayfa(lar):** {', '.join(f['expected_urls']) or '(yok: out_of_scope)'}\n"
            f"- **Beklenen sayfa derin aramada:** {deep}\n"
            f"- **Gelen sayfalar:**\n{retrieved}\n"
            f"- **Durum:** {f['status']} | kaynaklar: {', '.join(f['sources']) or '-'}\n"
            f"- **Cevap:** {answer}\n"
            f"- **Judge:** doğruluk={f.get('accuracy')} sadakat={f.get('faithfulness')} | {f.get('judge_reasoning') or '-'}\n"
        )
    return "\n".join(parts)


def _paths(config: str, provider: str) -> tuple[Path, Path, Path, Path]:
    results = RESULTS_DIR / f"{config}-full-{provider}.json"
    labels = Path(f"eval/error_labels-{config}.csv")
    dossier = RESULTS_DIR / f"errors-{config}.md"
    summary = RESULTS_DIR / f"errors-{config}.json"
    return results, labels, dossier, summary


def _load_rows(path: Path) -> tuple[list[dict], int]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return report["per_question"], report["k"]


def prepare(config_name: str, provider: str, force: bool) -> None:
    results, labels, dossier, _ = _paths(config_name, provider)
    rows, k = _load_rows(results)
    failures = select_failures(rows, k)

    deep_config = load_config(config_name).model_copy(update={"top_k": DEEP_K})
    llm = make_llm("rewrite", provider, LLM_SEED) if deep_config.rewrite else None
    searcher = make_searcher(deep_config, llm)
    failures = add_deep_ranks(failures, lambda question: [hit.chunk.url for hit in searcher(question).hits])

    write_label_template(labels, failures, force=force)  # first: never lose existing labels
    dossier.write_text(build_dossier(failures), encoding="utf-8")
    kinds = Counter(kind for f in failures for kind in f["kinds"])
    logger.info("%d failures of %d questions %s", len(failures), len(rows), dict(kinds))
    logger.info("read %s, then fill cause and reason in %s", dossier, labels)


def report(config_name: str, provider: str) -> None:
    results, labels_path, _, summary_path = _paths(config_name, provider)
    rows, k = _load_rows(results)
    failures = select_failures(rows, k)
    summary = summarize_causes(failures, load_labels(labels_path, allow_unlabeled=True))
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("%d failures, %d unlabeled", summary["n_failures"], len(summary["unlabeled"]))
    for cause, count in summary["counts"].items():
        logger.info("  %2d  %s", count, cause)
    logger.info("wrote %s", summary_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "report"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--provider", choices=["ollama", "groq"], default="groq")
    parser.add_argument("--force", action="store_true", help="prepare: overwrite an existing label file")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.config, args.provider, args.force)
    else:
        report(args.config, args.provider)


if __name__ == "__main__":
    main()
