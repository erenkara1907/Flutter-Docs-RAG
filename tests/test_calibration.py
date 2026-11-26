import pytest

from eval.calibration import (
    agreement,
    build_report,
    build_sheet,
    load_human_scores,
    select_sample,
    write_template,
)
from eval.judge import RUBRIC


def row(qid: str, accuracy: int = 5, faithfulness: int = 5, **extra) -> dict:
    return {
        "id": qid, "question": f"question {qid}", "answer": f"answer {qid}", "judged": True,
        "accuracy": accuracy, "faithfulness": faithfulness, "judge_reasoning": f"reason {qid}", **extra,
    }


def many_rows() -> list[dict]:
    high = [row(f"h{i:02d}") for i in range(30)]
    low = [row(f"l{i:02d}", accuracy=2) for i in range(4)] + [row("m00", faithfulness=3), row("m01", accuracy=3)]
    return high + low


class TestSelectSample:
    def test_returns_n_distinct_rows_from_the_input(self):
        sample = select_sample(many_rows(), n=20, seed=1, low_quota=6)
        ids = [r["id"] for r in sample]
        assert len(sample) == 20 and len(set(ids)) == 20
        assert set(ids) <= {r["id"] for r in many_rows()}

    def test_same_seed_gives_the_same_sample_in_the_same_order(self):
        assert select_sample(many_rows(), 20, seed=7) == select_sample(many_rows(), 20, seed=7)

    def test_different_seed_gives_a_different_sample(self):
        assert select_sample(many_rows(), 20, seed=1) != select_sample(many_rows(), 20, seed=2)

    def test_low_scoring_rows_are_over_represented_up_to_the_quota(self):
        sample = select_sample(many_rows(), n=20, seed=3, low_quota=6)
        low_ids = {r["id"] for r in sample if min(r["accuracy"], r["faithfulness"]) <= 3}
        assert len(low_ids) == 6  # all six low rows exist and the quota is six

    def test_fewer_low_rows_than_the_quota_still_fills_the_sample(self):
        rows = [row(f"h{i}") for i in range(30)] + [row("l0", accuracy=1)]
        sample = select_sample(rows, n=10, seed=1, low_quota=6)
        assert len(sample) == 10 and "l0" in {r["id"] for r in sample}

    def test_asking_for_more_than_exists_returns_everything(self):
        assert len(select_sample([row("a"), row("b")], n=20, seed=1)) == 2

    def test_rows_that_were_not_judged_are_never_sampled(self):
        rows = [row("a"), {**row("b"), "judged": False}]
        assert [r["id"] for r in select_sample(rows, n=5, seed=1)] == ["a"]


class TestBuildSheet:
    def sheet(self):
        sample = [row("q1", accuracy=2, faithfulness=3), row("q2")]
        passages = {"q1": ["passage one", "passage two"], "q2": ["other passage"]}
        references = {"q1": "reference one", "q2": "reference two"}
        return build_sheet(sample, passages, references)

    def test_shows_question_reference_answer_and_numbered_passages(self):
        sheet = self.sheet()
        for text in ("question q1", "reference one", "answer q1", "[1] passage one", "[2] passage two", "[1] other passage"):
            assert text in sheet

    def test_uses_the_same_rubric_as_the_judge(self):
        assert RUBRIC in self.sheet()

    def test_never_reveals_the_judge_scores_or_reasoning(self):
        sheet = self.sheet()
        assert "reason q1" not in sheet and "reason q2" not in sheet

    def test_lists_every_sampled_question_once(self):
        assert self.sheet().count("question q1") == 1


class TestWriteTemplate:
    def test_creates_a_csv_with_blank_score_columns(self, tmp_path):
        path = tmp_path / "human_scores.csv"
        write_template(path, [row("q1"), row("q2")])
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "id,human_accuracy,human_faithfulness,notes"
        assert lines[1:] == ["q1,,,", "q2,,,"]

    def test_refuses_to_overwrite_scores_the_user_may_have_filled_in(self, tmp_path):
        path = tmp_path / "human_scores.csv"
        path.write_text("id,human_accuracy,human_faithfulness,notes\nq1,4,5,\n", encoding="utf-8")
        with pytest.raises(FileExistsError):
            write_template(path, [row("q1")])
        assert "q1,4,5" in path.read_text(encoding="utf-8")

    def test_force_overwrites(self, tmp_path):
        path = tmp_path / "human_scores.csv"
        path.write_text("old", encoding="utf-8")
        write_template(path, [row("q1")], force=True)
        assert path.read_text(encoding="utf-8").startswith("id,")


def write_csv(path, body: str) -> None:
    path.write_text("id,human_accuracy,human_faithfulness,notes\n" + body, encoding="utf-8")


class TestLoadHumanScores:
    def test_reads_scores_keyed_by_id(self, tmp_path):
        write_csv(tmp_path / "s.csv", "q1,4,5,fine\nq2,2,3,\n")
        assert load_human_scores(tmp_path / "s.csv") == {
            "q1": {"accuracy": 4, "faithfulness": 5},
            "q2": {"accuracy": 2, "faithfulness": 3},
        }

    @pytest.mark.parametrize("body", ["q1,,5,\n", "q1,4,,\n", "q1,0,5,\n", "q1,6,5,\n", "q1,four,5,\n", "q1,4.5,5,\n"])
    def test_blank_out_of_range_and_non_integer_scores_are_rejected(self, tmp_path, body):
        write_csv(tmp_path / "s.csv", body)
        with pytest.raises(ValueError, match="q1"):
            load_human_scores(tmp_path / "s.csv")

    def test_duplicate_ids_are_rejected(self, tmp_path):
        write_csv(tmp_path / "s.csv", "q1,4,5,\nq1,3,3,\n")
        with pytest.raises(ValueError, match="duplicate"):
            load_human_scores(tmp_path / "s.csv")

    def test_missing_file_is_reported(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_human_scores(tmp_path / "nope.csv")


class TestAgreement:
    def test_hand_computed_example(self):
        # differences (judge - human): 0, +1, -2, 0
        result = agreement(human=[5, 4, 3, 2], judge=[5, 5, 1, 2])
        assert result["exact"] == 0.5
        assert result["within_1"] == 0.75
        assert result["mean_abs_diff"] == 0.75
        assert result["bias"] == -0.25
        assert result["n"] == 4

    def test_perfect_agreement(self):
        result = agreement([1, 2, 3], [1, 2, 3])
        assert (result["exact"], result["within_1"], result["bias"]) == (1.0, 1.0, 0.0)

    def test_a_lenient_judge_has_positive_bias(self):
        assert agreement([2, 3], [4, 5])["bias"] == 2.0

    def test_lengths_must_match(self):
        with pytest.raises(ValueError):
            agreement([1, 2], [1])

    def test_empty_input_is_an_error(self):
        with pytest.raises(ValueError):
            agreement([], [])


class TestBuildReport:
    def human(self):
        return {"q1": {"accuracy": 5, "faithfulness": 5}, "q2": {"accuracy": 2, "faithfulness": 4}}

    def rows(self):
        return [row("q1", accuracy=5, faithfulness=5), row("q2", accuracy=5, faithfulness=4)]

    def test_computes_agreement_per_metric(self):
        report = build_report(self.human(), self.rows())
        assert report["accuracy"]["exact"] == 0.5 and report["faithfulness"]["exact"] == 1.0

    def test_flags_disagreements_of_two_or_more_with_the_judge_reasoning(self):
        report = build_report(self.human(), self.rows())
        assert report["disagreements"] == [
            {"id": "q2", "metric": "accuracy", "human": 2, "judge": 5, "judge_reasoning": "reason q2"}
        ]

    def test_threshold_is_met_only_when_both_metrics_reach_seventy_percent_within_one(self):
        assert build_report(self.human(), self.rows())["meets_threshold"] is False
        good = {"q1": {"accuracy": 5, "faithfulness": 5}, "q2": {"accuracy": 4, "faithfulness": 4}}
        assert build_report(good, self.rows())["meets_threshold"] is True

    def test_a_human_score_without_a_judged_row_is_an_error(self):
        with pytest.raises(ValueError, match="q9"):
            build_report({"q9": {"accuracy": 3, "faithfulness": 3}}, self.rows())
