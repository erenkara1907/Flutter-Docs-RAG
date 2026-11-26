import json

import pytest

from eval.report import build_full_table, build_markdown, build_retrieval_table, load_reports, plot_ablation


def retrieval(config, hit=0.8, mrr=0.7, tr_hit=0.5, latency=100.0) -> dict:
    return {
        "config": config, "stage": "retrieval", "k": 5, "mean_latency_ms": latency,
        "overall": {"hit@5": hit, "recall@5": 0.6, "mrr": mrr, "ndcg@5": 0.65, "n": 65},
        "by_category": {"tr": {"hit@5": tr_hit, "mrr": 0.4, "n": 10}},
    }


def full(config, accuracy=4.5) -> dict:
    return {
        "config": config, "stage": "full",
        "overall": {
            "accuracy": accuracy, "faithfulness": 4.9, "source_accuracy": 0.9, "refusal_accuracy": 0.9,
            "answered_rate": 0.85, "mean_latency_ms": 1000.0, "mean_llm_calls": 1.5,
        },
    }


def write(path, report) -> None:
    path.write_text(json.dumps(report), encoding="utf-8")


class TestLoadReports:
    def test_orders_by_the_ablation_sequence_not_by_file_name(self, tmp_path):
        for name in ("r5", "r0", "r4v", "r2a"):
            write(tmp_path / f"{name}-retrieval.json", retrieval(name))
        assert [r["config"] for r in load_reports(tmp_path, "retrieval")] == ["r0", "r2a", "r4v", "r5"]

    def test_missing_configs_are_skipped(self, tmp_path):
        write(tmp_path / "r0-retrieval.json", retrieval("r0"))
        assert len(load_reports(tmp_path, "retrieval")) == 1

    def test_full_reports_are_found_by_their_own_suffix(self, tmp_path):
        write(tmp_path / "r0-full-groq.json", full("r0"))
        write(tmp_path / "r0-retrieval.json", retrieval("r0"))
        assert [r["stage"] for r in load_reports(tmp_path, "full")] == ["full"]

    def test_no_reports_is_an_error(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_reports(tmp_path, "retrieval")


class TestRetrievalTable:
    def test_has_one_row_per_config_with_three_decimals(self):
        table = build_retrieval_table([retrieval("r0", hit=0.7231), retrieval("r1", hit=0.8)])
        lines = table.splitlines()
        assert lines[0].startswith("| Config |") and len(lines) == 4
        assert "| r0 | 0.723 |" in lines[2]

    def test_turkish_hit_and_latency_are_included(self):
        row = build_retrieval_table([retrieval("r0", tr_hit=0.2, latency=640.4)]).splitlines()[2]
        assert "0.200" in row and "640" in row


    def test_a_report_measured_before_latency_was_recorded_shows_a_dash(self):
        old = retrieval("r0")
        del old["mean_latency_ms"]
        assert build_retrieval_table([old]).splitlines()[2].endswith("| - |")


class TestFullTable:
    def test_rows_show_answer_quality_metrics(self):
        table = build_full_table([full("r0", accuracy=4.46), full("r4v", accuracy=4.56)])
        assert "4.46" in table and "4.56" in table and "r4v" in table


class TestMarkdown:
    def test_places_the_chart_before_the_tables(self):
        text = build_markdown([retrieval("r0")], [full("r0")], "ablation.png")
        assert text.index("ablation.png") < text.index("| Config |")


class TestPlot:
    def test_writes_a_png(self, tmp_path):
        path = tmp_path / "out" / "ablation.png"
        plot_ablation([retrieval("r0"), retrieval("r1", hit=0.9)], path)
        assert path.read_bytes()[:4] == b"\x89PNG"
