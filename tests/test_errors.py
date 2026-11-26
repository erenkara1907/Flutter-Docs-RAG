import pytest

from eval.errors import (
    CAUSES,
    add_deep_ranks,
    build_dossier,
    expected_rank,
    failure_kinds,
    load_labels,
    select_failures,
    suggest_cause,
    summarize_causes,
    write_label_template,
)


def url(i: int) -> str:
    return f"https://docs.flutter.dev/page{i}"


def row(qid="q1", category="single", answerable=True, status="answered", hit=1.0, accuracy=5, **extra) -> dict:
    base = {
        "id": qid, "category": category, "lang": "en", "question": f"question {qid}", "answerable": answerable,
        "status": status, "answer": "an answer", "sources": [url(0)], "search_query": None,
        "expected_urls": [url(0)] if answerable else [], "retrieved_urls": [url(1), url(2)],
        "judged": accuracy is not None, "accuracy": accuracy, "faithfulness": 5 if accuracy else None,
        "judge_reasoning": "because",
    }
    if answerable:
        base["hit@5"] = hit
    return {**base, **extra}


class TestFailureKinds:
    def test_a_good_answer_is_not_a_failure(self):
        assert failure_kinds(row(), k=5) == []

    def test_retrieval_miss_when_hit_is_zero(self):
        assert "retrieval_miss" in failure_kinds(row(hit=0.0), k=5)

    def test_low_accuracy_is_two_or_less(self):
        assert "low_accuracy" in failure_kinds(row(accuracy=2), k=5)
        assert failure_kinds(row(accuracy=3), k=5) == []

    def test_unjudged_rows_do_not_crash(self):
        assert failure_kinds(row(status="not_found", accuracy=None), k=5) == ["refused"]

    def test_refusing_an_answerable_question_is_a_failure(self):
        assert failure_kinds(row(status="not_found", accuracy=None, hit=1.0), k=5) == ["refused"]

    def test_a_miss_that_was_refused_has_both_kinds(self):
        kinds = failure_kinds(row(status="not_found", accuracy=None, hit=0.0), k=5)
        assert kinds == ["retrieval_miss", "refused"]

    def test_answering_an_out_of_scope_question_is_hallucination(self):
        assert failure_kinds(row(category="out_of_scope", answerable=False, accuracy=None), k=5) == ["hallucinated"]

    def test_correctly_refused_out_of_scope_question_is_fine(self):
        oos = row(category="out_of_scope", answerable=False, status="not_found", accuracy=None)
        assert failure_kinds(oos, k=5) == []

    def test_uses_the_hit_key_of_the_requested_k(self):
        assert "retrieval_miss" in failure_kinds({**row(), "hit@3": 0.0}, k=3)


class TestSelectFailures:
    def test_keeps_order_and_adds_kinds_without_touching_the_input(self):
        rows = [row("q1"), row("q2", hit=0.0), row("q3", accuracy=1)]
        snapshot = [dict(r) for r in rows]
        failures = select_failures(rows, k=5)
        assert [f["id"] for f in failures] == ["q2", "q3"]
        assert failures[0]["kinds"] == ["retrieval_miss"] and failures[1]["kinds"] == ["low_accuracy"]
        assert rows == snapshot


class TestExpectedRank:
    def test_best_rank_among_expected_pages(self):
        assert expected_rank([url(5), url(3), url(1)], [url(1), url(3)]) == 2

    def test_none_when_absent(self):
        assert expected_rank([url(5)], [url(1)]) is None

    def test_none_without_expected_pages(self):
        assert expected_rank([url(5)], []) is None


class TestAddDeepRanks:
    def test_records_where_the_expected_page_would_have_ranked(self):
        failures = select_failures([row("q1", hit=0.0)], k=5)
        deep = lambda question: [url(7), url(8), url(0)]
        assert add_deep_ranks(failures, deep)[0]["expected_rank"] == 3

    def test_none_when_even_the_deep_search_misses(self):
        failures = select_failures([row("q1", hit=0.0)], k=5)
        assert add_deep_ranks(failures, lambda q: [url(9)])[0]["expected_rank"] is None

    def test_questions_without_expected_pages_are_not_searched(self):
        failures = select_failures([row("q1", category="out_of_scope", answerable=False, accuracy=None)], k=5)

        def deep(question):
            raise AssertionError("must not search")

        assert add_deep_ranks(failures, deep)[0]["expected_rank"] is None

    def test_does_not_mutate_the_failures_it_is_given(self):
        failures = select_failures([row("q1", hit=0.0)], k=5)
        add_deep_ranks(failures, lambda q: [url(0)])
        assert "expected_rank" not in failures[0]


class TestSuggestCause:
    def failure(self, **kwargs):
        return {**row(**kwargs), "kinds": failure_kinds(row(**kwargs), 5), "expected_rank": kwargs.get("rank")}

    def test_hallucination(self):
        f = self.failure(category="out_of_scope", answerable=False, accuracy=None)
        assert suggest_cause(f) == "hallucinated_answer"

    def test_miss_with_a_near_rank_is_a_ranking_problem(self):
        assert suggest_cause(self.failure(hit=0.0, rank=12)) == "retrieval_ranking"

    def test_miss_far_beyond_the_deep_search_is_a_semantic_gap(self):
        assert suggest_cause(self.failure(hit=0.0, rank=None)) == "retrieval_semantic_gap"

    def test_turkish_miss_is_a_language_gap(self):
        f = self.failure(hit=0.0, rank=None)
        assert suggest_cause({**f, "lang": "tr", "search_query": None}) == "language_gap"

    def test_causes_that_need_reading_get_no_suggestion(self):
        assert suggest_cause(self.failure(accuracy=2)) is None
        assert suggest_cause(self.failure(status="not_found", accuracy=None)) is None


class TestLabelTemplate:
    def failures(self):
        return add_deep_ranks(select_failures([row("q1", hit=0.0), row("q2", accuracy=2)], k=5), lambda q: [url(9)])

    def test_has_one_line_per_failure_with_kinds_and_a_suggestion(self, tmp_path):
        path = tmp_path / "labels.csv"
        write_label_template(path, self.failures())
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "id,kinds,suggested_cause,cause,reason"
        assert lines[1] == "q1,retrieval_miss,retrieval_semantic_gap,,"
        assert lines[2] == "q2,low_accuracy,,,"

    def test_never_overwrites_existing_labels(self, tmp_path):
        path = tmp_path / "labels.csv"
        path.write_text("id,kinds,suggested_cause,cause,reason\nq1,x,,chunking,mine\n", encoding="utf-8")
        with pytest.raises(FileExistsError):
            write_label_template(path, self.failures())
        assert "mine" in path.read_text(encoding="utf-8")

    def test_force_overwrites(self, tmp_path):
        path = tmp_path / "labels.csv"
        path.write_text("old", encoding="utf-8")
        write_label_template(path, self.failures(), force=True)
        assert path.read_text(encoding="utf-8").startswith("id,kinds")


def write_labels(path, body: str) -> None:
    path.write_text("id,kinds,suggested_cause,cause,reason\n" + body, encoding="utf-8")


class TestLoadLabels:
    def test_reads_cause_and_reason_by_id(self, tmp_path):
        write_labels(tmp_path / "l.csv", "q1,retrieval_miss,,chunking,the page was split badly\n")
        assert load_labels(tmp_path / "l.csv") == {"q1": {"cause": "chunking", "reason": "the page was split badly"}}

    @pytest.mark.parametrize("body", ["q1,k,,,reason\n", "q1,k,,chunking,\n", "q1,k,,made_up_cause,reason\n"])
    def test_blank_or_unknown_labels_are_rejected(self, tmp_path, body):
        write_labels(tmp_path / "l.csv", body)
        with pytest.raises(ValueError, match="q1"):
            load_labels(tmp_path / "l.csv")

    def test_rows_still_blank_can_be_skipped_while_labeling_is_in_progress(self, tmp_path):
        write_labels(tmp_path / "l.csv", "q1,k,,chunking,done\nq2,k,,,\n")
        assert list(load_labels(tmp_path / "l.csv", allow_unlabeled=True)) == ["q1"]

    def test_a_half_filled_row_is_rejected_even_when_skipping_blanks(self, tmp_path):
        write_labels(tmp_path / "l.csv", "q2,k,,chunking,\n")
        with pytest.raises(ValueError, match="q2"):
            load_labels(tmp_path / "l.csv", allow_unlabeled=True)

    def test_duplicate_ids_are_rejected(self, tmp_path):
        write_labels(tmp_path / "l.csv", "q1,k,,chunking,a\nq1,k,,chunking,b\n")
        with pytest.raises(ValueError, match="duplicate"):
            load_labels(tmp_path / "l.csv")

    def test_every_cause_in_the_list_is_accepted(self, tmp_path):
        body = "".join(f"q{i},k,,{cause},reason\n" for i, cause in enumerate(CAUSES))
        write_labels(tmp_path / "l.csv", body)
        assert len(load_labels(tmp_path / "l.csv")) == len(CAUSES)


class TestSummarizeCauses:
    def failures(self):
        return select_failures([row(f"q{i}", hit=0.0) for i in range(1, 6)], k=5)

    def labels(self, causes):
        return {f"q{i}": {"cause": c, "reason": "r"} for i, c in enumerate(causes, start=1)}

    def test_counts_causes_most_common_first(self):
        labels = self.labels(["chunking", "retrieval_ranking", "retrieval_ranking", "retrieval_ranking", "chunking"])
        summary = summarize_causes(self.failures(), labels)
        assert summary["counts"] == {"retrieval_ranking": 3, "chunking": 2}
        assert [t["cause"] for t in summary["top3"]] == ["retrieval_ranking", "chunking"]

    def test_ties_are_broken_by_name_so_the_result_is_stable(self):
        summary = summarize_causes(self.failures()[:2], self.labels(["chunking", "language_gap"]))
        assert list(summary["counts"]) == ["chunking", "language_gap"]

    def test_top3_lists_example_ids(self):
        labels = self.labels(["chunking", "chunking", "model_error", "model_error", "model_error"])
        top = summarize_causes(self.failures(), labels)["top3"]
        assert top[0] == {"cause": "model_error", "count": 3, "ids": ["q3", "q4", "q5"]}

    def test_reports_failures_that_still_have_no_label(self):
        summary = summarize_causes(self.failures(), self.labels(["chunking", "chunking"]))
        assert summary["unlabeled"] == ["q3", "q4", "q5"]

    def test_a_label_for_a_non_failure_is_an_error(self):
        with pytest.raises(ValueError, match="q99"):
            summarize_causes(self.failures(), {"q99": {"cause": "chunking", "reason": "r"}})


class TestBuildDossier:
    def test_shows_what_is_needed_to_judge_the_failure(self):
        failure = {**select_failures([row("q7", hit=0.0, search_query="rewritten words")], k=5)[0], "expected_rank": 14}
        text = build_dossier([failure])
        for needle in ("q7", "question q7", "rewritten words", url(0), url(1), "14", "an answer", "because", "retrieval_miss"):
            assert needle in text

    def test_long_answers_are_cut(self):
        failure = select_failures([row("q1", accuracy=1, answer="x" * 5000)], k=5)[0]
        assert "x" * 1500 not in build_dossier([failure])
