"""Turn the saved evaluation results into docs/EVAL.md and docs/ablation.png.

    uv run python -m eval.report
"""

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no window: the chart is only written to a file
import matplotlib.pyplot as plt  # noqa: E402

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("eval/results")
DOCS_DIR = Path("docs")
CONFIG_ORDER = ("r0", "r1", "r2a", "r2b", "r3", "r4", "r4v", "r5", "r6", "r7")
GLOB_BY_STAGE = {"retrieval": "*-retrieval.json", "full": "*-full-*.json"}

RETRIEVAL_NOTE = (
    "r4, r4v ve r5 bu tabloda rewrite/rerank için yerel `llama3.2` ile, r7 ise Groq `gpt-oss-20b` ile ölçüldü; "
    "tam değerlendirme tablosu da Groq modelleriyle. Bu ölçümler birbirine birebir kıyaslanmamalı. "
    "r6 (yalnız BM25) ve r7 (BM25 + yeniden yazma) canlı sitenin kullandığı vektörsüz yoldur. "
    "Out-of-scope sorular retrieval skoruna girmez (n=65)."
)


def load_reports(results_dir: Path, stage: str) -> list[dict]:
    """Saved reports of one stage, in ablation order. Configs without a report are skipped."""
    reports = [json.loads(p.read_text(encoding="utf-8")) for p in Path(results_dir).glob(GLOB_BY_STAGE[stage])]
    if not reports:
        raise FileNotFoundError(f"no {stage} reports in {results_dir}; run eval.run first")
    return sorted(reports, key=lambda r: CONFIG_ORDER.index(r["config"]))


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _latency(report: dict) -> str:
    """Older reports were saved before latency was recorded; show a dash rather than guess."""
    value = report.get("mean_latency_ms")
    return "-" if value is None else f"{value:.1f}"


def build_retrieval_table(reports: list[dict]) -> str:
    rows = [
        [
            r["config"], f"{r['overall']['hit@5']:.3f}", f"{r['overall']['recall@5']:.3f}",
            f"{r['overall']['mrr']:.3f}", f"{r['overall']['ndcg@5']:.3f}",
            f"{r['by_category']['tr']['hit@5']:.3f}", _latency(r),
        ]
        for r in reports
    ]
    return _table(["Config", "Hit@5", "Recall@5", "MRR", "nDCG@5", "tr Hit@5", "ms/soru"], rows)


def build_full_table(reports: list[dict]) -> str:
    rows = [
        [
            r["config"], f"{r['overall']['accuracy']:.2f}", f"{r['overall']['faithfulness']:.2f}",
            f"{r['overall']['source_accuracy']:.3f}", f"{r['overall']['refusal_accuracy']:.3f}",
            f"{r['overall']['answered_rate']:.2f}", f"{r['overall']['mean_latency_ms']:.0f}",
            f"{r['overall']['mean_llm_calls']:.1f}",
        ]
        for r in reports
    ]
    header = ["Config", "Accuracy", "Faithfulness", "Kaynak doğr.", "Red doğruluğu", "Cevaplanan", "ms/soru", "LLM çağrısı"]
    return _table(header, rows)


def build_markdown(retrieval: list[dict], full: list[dict], chart: str) -> str:
    return (
        "# Değerlendirme sonuçları\n\n"
        f"![Ablation]({chart})\n\n"
        "## Retrieval (sayfa bazlı, k=5)\n\n"
        f"{build_retrieval_table(retrieval)}\n\n{RETRIEVAL_NOTE}\n\n"
        "## Tam hat (cevap + judge)\n\n"
        f"{build_full_table(full)}\n\n"
        "Accuracy ve faithfulness yalnız cevaplanan sorular üzerinden hesaplanır; judge bir LLM'dir.\n"
    )


def plot_ablation(reports: list[dict], path: Path) -> None:
    configs = [r["config"] for r in reports]
    series = [
        ("Hit@5", [r["overall"]["hit@5"] for r in reports], "-", "o"),
        ("MRR", [r["overall"]["mrr"] for r in reports], "-", "s"),
        ("tr Hit@5", [r["by_category"]["tr"]["hit@5"] for r in reports], "--", "o"),
        ("tr MRR", [r["by_category"]["tr"]["mrr"] for r in reports], "--", "s"),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for label, values, style, marker in series:
        ax.plot(configs, values, style, marker=marker, label=label)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Config")
    ax.set_ylabel("Skor")
    ax.set_title("Ablation: retrieval kalitesi")
    ax.grid(alpha=0.3)
    ax.legend()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    retrieval = load_reports(RESULTS_DIR, "retrieval")
    full = load_reports(RESULTS_DIR, "full")
    plot_ablation(retrieval, DOCS_DIR / "ablation.png")
    (DOCS_DIR / "EVAL.md").write_text(build_markdown(retrieval, full, "ablation.png"), encoding="utf-8")
    logger.info("wrote %s and %s", DOCS_DIR / "EVAL.md", DOCS_DIR / "ablation.png")


if __name__ == "__main__":
    main()
