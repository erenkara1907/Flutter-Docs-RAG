"""Judge calibration: do the judge's scores agree with a human's?

    python -m eval.calibration prepare   # writes the worksheet and an empty score sheet
    python -m eval.calibration report    # compares the filled-in sheet with the judge

The worksheet never shows the judge's scores, so the human scores blind.
"""

import argparse
import csv
import json
import logging
import random
from pathlib import Path

from eval.golden import DEFAULT_GOLDEN_PATH, load_golden
from eval.judge import RUBRIC
from eval.metrics import unique_urls
from rag.config import load_config
from rag.pipeline import make_searcher

logger = logging.getLogger(__name__)

SOURCE_RESULTS = Path("eval/results/r0-full-groq.json")
SHEET_PATH = Path("eval/calibration_sheet.md")
SCORES_PATH = Path("eval/human_scores.csv")
REPORT_PATH = Path("eval/results/calibration.json")
SOURCE_CONFIG = "r0"  # no rewrite or rerank, so retrieval is deterministic and can be replayed

SAMPLE_SIZE = 20
SAMPLE_SEED = 42
LOW_QUOTA = 6  # judge scores near the ceiling say little, so some low-scored answers are included
LOW_SCORE_MAX = 3
THRESHOLD = 0.70  # share of scores within one point that counts as "the judge is usable"
BIG_DISAGREEMENT = 2
CSV_HEADER = ["id", "human_accuracy", "human_faithfulness", "notes"]


def _is_low(row: dict) -> bool:
    return min(row["accuracy"], row["faithfulness"]) <= LOW_SCORE_MAX


def select_sample(rows: list[dict], n: int = SAMPLE_SIZE, seed: int = SAMPLE_SEED, low_quota: int = LOW_QUOTA) -> list[dict]:
    """n judged rows, up to `low_quota` of them low-scored, the rest random. Seeded and shuffled."""
    judged = [row for row in rows if row["judged"]]
    low = [row for row in judged if _is_low(row)]
    rest = [row for row in judged if not _is_low(row)]
    rng = random.Random(seed)
    rng.shuffle(low)
    rng.shuffle(rest)

    n_low = min(low_quota, len(low))
    picked = low[:n_low] + rest[: max(0, n - n_low)]
    if len(picked) < n:  # not enough ordinary rows: top up with the remaining low ones
        picked += low[n_low : n_low + (n - len(picked))]
    picked = picked[:n]
    rng.shuffle(picked)
    return picked


def build_sheet(sample: list[dict], passages: dict[str, list[str]], references: dict[str, str]) -> str:
    parts = [
        "# Judge kalibrasyonu: elle puanlama formu",
        "Her cevap için iki puan ver (1-5) ve `eval/human_scores.csv` dosyasına yaz. "
        "Judge'ın puanlarını görmüyorsun, bilerek. Ölçek judge'a verilenle aynıdır:",
        f"```\n{RUBRIC}\n```",
    ]
    for number, row in enumerate(sample, start=1):
        numbered = "\n\n".join(f"[{i}] {text}" for i, text in enumerate(passages[row["id"]], start=1))
        parts.append(
            f"---\n## {number}. (id: {row['id']})\n\n"
            f"**Soru:** {row['question']}\n\n"
            f"**Referans cevap:** {references[row['id']]}\n\n"
            f"**Sistemin cevabı:** {row['answer']}\n\n"
            f"**Modele verilen pasajlar:**\n\n{numbered}"
        )
    return "\n\n".join(parts) + "\n"


def write_template(path: Path, sample: list[dict], force: bool = False) -> None:
    path = Path(path)
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists and may hold your scores; pass --force to overwrite")
    lines = [",".join(CSV_HEADER)] + [f"{row['id']},,," for row in sample]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_score(value: str | None, qid: str, field: str) -> int:
    text = (value or "").strip()
    if text not in {"1", "2", "3", "4", "5"}:
        raise ValueError(f"{qid}: {field} must be an integer from 1 to 5, got {text!r}")
    return int(text)


def load_human_scores(path: Path) -> dict[str, dict[str, int]]:
    scores: dict[str, dict[str, int]] = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for record in csv.DictReader(f):
            qid = (record.get("id") or "").strip()
            if qid in scores:
                raise ValueError(f"duplicate id {qid}")
            scores[qid] = {
                "accuracy": _parse_score(record.get("human_accuracy"), qid, "human_accuracy"),
                "faithfulness": _parse_score(record.get("human_faithfulness"), qid, "human_faithfulness"),
            }
    return scores


def agreement(human: list[int], judge: list[int]) -> dict:
    if len(human) != len(judge):
        raise ValueError("human and judge need the same number of scores")
    if not human:
        raise ValueError("no scores to compare")
    n = len(human)
    diffs = [j - h for h, j in zip(human, judge)]
    return {
        "n": n,
        "exact": sum(d == 0 for d in diffs) / n,
        "within_1": sum(abs(d) <= 1 for d in diffs) / n,
        "mean_abs_diff": sum(abs(d) for d in diffs) / n,
        "bias": sum(diffs) / n,  # judge minus human; positive means the judge is more generous
    }


def build_report(human: dict[str, dict[str, int]], rows: list[dict]) -> dict:
    by_id = {row["id"]: row for row in rows if row["judged"]}
    for qid in human:
        if qid not in by_id:
            raise ValueError(f"no judged result for {qid}")

    ids = sorted(human)
    report: dict = {}
    disagreements = []
    for metric in ("accuracy", "faithfulness"):
        humans = [human[qid][metric] for qid in ids]
        judges = [by_id[qid][metric] for qid in ids]
        report[metric] = agreement(humans, judges)
        disagreements += [
            {"id": qid, "metric": metric, "human": h, "judge": j, "judge_reasoning": by_id[qid]["judge_reasoning"]}
            for qid, h, j in zip(ids, humans, judges)
            if abs(j - h) >= BIG_DISAGREEMENT
        ]
    report["disagreements"] = sorted(disagreements, key=lambda d: (d["id"], d["metric"]))
    report["meets_threshold"] = all(report[m]["within_1"] >= THRESHOLD for m in ("accuracy", "faithfulness"))
    report["threshold"] = THRESHOLD
    return report


def _passages_for(sample: list[dict]) -> dict[str, list[str]]:
    """Replay retrieval for each sampled question and check it matches what the judge saw."""
    searcher = make_searcher(load_config(SOURCE_CONFIG))
    passages = {}
    for row in sample:
        hits = searcher(row["question"]).hits
        if unique_urls([hit.chunk.url for hit in hits]) != row["retrieved_urls"]:
            raise RuntimeError(f"retrieval for {row['id']} no longer matches the saved run; do not score this sheet")
        passages[row["id"]] = [hit.chunk.text for hit in hits]
    return passages


def prepare(force: bool) -> None:
    rows = json.loads(SOURCE_RESULTS.read_text(encoding="utf-8"))["per_question"]
    sample = select_sample(rows)
    references = {q.id: q.reference_answer for q in load_golden(DEFAULT_GOLDEN_PATH)}
    write_template(SCORES_PATH, sample, force=force)  # first, so an existing score sheet is never lost
    SHEET_PATH.write_text(build_sheet(sample, _passages_for(sample), references), encoding="utf-8")
    logger.info("wrote %s (read this) and %s (fill this in): %d answers", SHEET_PATH, SCORES_PATH, len(sample))


def report() -> None:
    rows = json.loads(SOURCE_RESULTS.read_text(encoding="utf-8"))["per_question"]
    result = build_report(load_human_scores(SCORES_PATH), rows)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for metric in ("accuracy", "faithfulness"):
        stats = result[metric]
        logger.info(
            "%s: exact %.0f%%, within 1 point %.0f%%, mean abs diff %.2f, bias %+.2f (n=%d)",
            metric, stats["exact"] * 100, stats["within_1"] * 100, stats["mean_abs_diff"], stats["bias"], stats["n"],
        )
    logger.info("threshold (%.0f%% within 1 point on both): %s", THRESHOLD * 100, "met" if result["meets_threshold"] else "NOT met")
    for item in result["disagreements"]:
        logger.info("  %s %s human=%d judge=%d | %s", item["id"], item["metric"], item["human"], item["judge"], item["judge_reasoning"][:140])
    logger.info("wrote %s", REPORT_PATH)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "report"])
    parser.add_argument("--force", action="store_true", help="prepare: overwrite an existing score sheet")
    args = parser.parse_args()
    prepare(args.force) if args.command == "prepare" else report()


if __name__ == "__main__":
    main()
