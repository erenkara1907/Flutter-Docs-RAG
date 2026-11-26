import json

import pytest

from eval.full import (
    CallCounter,
    ProgressStore,
    build_report,
    counted,
    refusal_correct,
    run_full,
    source_correct,
    summarize_rows,
)
from eval.golden import GoldenQuestion
from rag.answer import Answer, Source
from rag.chunk import Chunk
from rag.pipeline import SearchResult
from rag.retrieve import Hit


def url(i: int) -> str:
    return f"https://docs.flutter.dev/page{i}"


def question(qid="q1", category="single", expected=(0,), lang="en") -> GoldenQuestion:
    answerable = category != "out_of_scope"
    return GoldenQuestion(
        id=qid, category=category, lang=lang, question=f"question {qid}",
        expected_urls=[url(i) for i in expected] if answerable else [],
        reference_answer="reference", answerable=answerable,
    )


def answer(status="answered", sources=(0,)) -> Answer:
    return Answer(answer="text", status=status, sources=[Source(title="T", url=url(i)) for i in sources])


def hits(n=3) -> list[Hit]:
    return [
        Hit(chunk=Chunk(url=url(i), title=f"T{i}", section="ui", heading="", text=f"passage {i}"), score=1.0)
        for i in range(n)
    ]


class TestSourceCorrect:
    def test_true_when_a_cited_page_is_expected(self):
        assert source_correct(answer(sources=(0, 5)), question(expected=(0,))) is True

    def test_false_when_no_cited_page_is_expected(self):
        assert source_correct(answer(sources=(5,)), question(expected=(0,))) is False

    def test_multi_question_needs_only_one_overlap(self):
        assert source_correct(answer(sources=(1,)), question(category="multi", expected=(0, 1))) is True

    def test_undefined_when_nothing_was_answered(self):
        assert source_correct(answer(status="not_found", sources=()), question()) is None

    def test_undefined_for_out_of_scope_questions(self):
        assert source_correct(answer(), question(category="out_of_scope")) is None


class TestRefusalCorrect:
    def test_answerable_question_should_be_answered(self):
        assert refusal_correct(answer("answered"), question()) is True
        assert refusal_correct(answer("not_found", ()), question()) is False

    def test_out_of_scope_question_should_be_not_found(self):
        oos = question(category="out_of_scope")
        assert refusal_correct(answer("not_found", ()), oos) is True
        assert refusal_correct(answer("answered"), oos) is False

    def test_a_broken_reply_is_not_a_correct_refusal(self):
        assert refusal_correct(answer("invalid_reply", ()), question(category="out_of_scope")) is False


class TestCallCounter:
    def test_counts_every_call_and_passes_the_reply_through(self):
        counter = CallCounter()
        llm = counted(lambda prompt: prompt.upper(), counter)
        assert llm("a") == "A" and llm("b") == "B"
        assert counter.calls == 2

    def test_accumulates_wait_time(self):
        counter = CallCounter()
        counter.add_wait(1.5)
        counter.add_wait(2.0)
        assert counter.waited_s == 3.5


class TestProgressStore:
    def test_missing_file_means_nothing_done(self, tmp_path):
        assert ProgressStore(tmp_path / "p.jsonl").load() == {}

    def test_rows_survive_a_round_trip_keyed_by_id(self, tmp_path):
        store = ProgressStore(tmp_path / "p.jsonl")
        store.append({"id": "q1", "status": "answered"})
        store.append({"id": "q2", "status": "not_found"})
        assert ProgressStore(tmp_path / "p.jsonl").load() == {
            "q1": {"id": "q1", "status": "answered"},
            "q2": {"id": "q2", "status": "not_found"},
        }

    def test_clear_removes_the_file(self, tmp_path):
        store = ProgressStore(tmp_path / "p.jsonl")
        store.append({"id": "q1"})
        store.clear()
        assert store.load() == {}


def reply(**fields) -> str:
    return json.dumps({"answer": "Use Expanded.", "used_sources": [1], "found_in_docs": True, **fields})


JUDGE_OK = json.dumps({"reasoning": "fine", "accuracy": 4, "faithfulness": 5})


class Harness:
    """Fakes for everything outside eval/full.py."""

    def __init__(self, tmp_path, answer_reply=None, judge_reply=JUDGE_OK, search_hits=None, is_flutter=True):
        self.counter = CallCounter()
        self.searched: list[str] = []
        self.judged: list[str] = []
        self.store = ProgressStore(tmp_path / "progress.jsonl")
        self._hits = hits() if search_hits is None else search_hits
        self._is_flutter = is_flutter
        self._answer_reply = answer_reply or reply()
        self._judge_reply = judge_reply
        self.answer_llm = counted(lambda prompt: self._answer_reply, self.counter)

    def searcher(self, text):
        self.searched.append(text)
        return SearchResult(hits=self._hits, search_query=f"rewritten {text}", is_flutter_question=self._is_flutter)

    def judge_llm(self, prompt):
        self.judged.append(prompt)
        return self._judge_reply

    def run(self, questions, clock=None):
        kwargs = {} if clock is None else {"clock": clock}
        return run_full(questions, self.searcher, self.answer_llm, self.judge_llm, self.counter, self.store, k=5, **kwargs)


class TestRunFull:
    def test_answered_question_is_judged_and_scored(self, tmp_path):
        row = Harness(tmp_path).run([question()])[0]
        assert (row["status"], row["accuracy"], row["faithfulness"], row["judged"]) == ("answered", 4, 5, True)
        assert row["source_correct"] is True and row["refusal_correct"] is True
        assert row["sources"] == [url(0)] and row["search_query"] == "rewritten question q1"
        assert row["hit@5"] == 1.0

    def test_the_judge_sees_the_passages_the_answerer_saw(self, tmp_path):
        harness = Harness(tmp_path)
        harness.run([question()])
        assert "passage 0" in harness.judged[0] and "passage 2" in harness.judged[0]

    def test_out_of_scope_refusal_is_correct_and_not_judged(self, tmp_path):
        harness = Harness(tmp_path, answer_reply=reply(answer="", used_sources=[], found_in_docs=False))
        row = harness.run([question(category="out_of_scope")])[0]
        assert row["refusal_correct"] is True and row["judged"] is False and harness.judged == []
        assert "hit@5" not in row

    def test_hallucinated_answer_to_an_out_of_scope_question_is_flagged_not_judged(self, tmp_path):
        harness = Harness(tmp_path)
        row = harness.run([question(category="out_of_scope")])[0]
        assert row["status"] == "answered" and row["refusal_correct"] is False and harness.judged == []

    def test_missed_answerable_question_has_no_judge_scores(self, tmp_path):
        harness = Harness(tmp_path, answer_reply=reply(answer="", used_sources=[], found_in_docs=False))
        row = harness.run([question()])[0]
        assert row["refusal_correct"] is False and row["accuracy"] is None and row["source_correct"] is None

    def test_unusable_judge_reply_is_recorded_as_not_judged(self, tmp_path):
        row = Harness(tmp_path, judge_reply="garbage").run([question()])[0]
        assert row["judged"] is False and row["accuracy"] is None and row["status"] == "answered"

    def test_non_flutter_question_skips_the_answer_model(self, tmp_path):
        harness = Harness(tmp_path, is_flutter=False)
        row = harness.run([question(category="out_of_scope")])[0]
        assert row["status"] == "not_found" and harness.counter.calls == 0

    def test_llm_calls_count_only_the_answer_side(self, tmp_path):
        harness = Harness(tmp_path)
        assert harness.run([question()])[0]["llm_calls"] == 1
        assert harness.judged  # the judge was used but is not counted

    def test_latency_excludes_time_spent_waiting_for_the_quota(self, tmp_path):
        harness = Harness(tmp_path)
        ticks = iter([0.0, 5.0])

        def clock():
            value = next(ticks)
            if value == 0.0:
                harness.counter.add_wait(2.0)  # a rate-limit pause happens inside the question
            return value

        assert harness.run([question()], clock=clock)[0]["latency_ms"] == 3000.0

    def test_progress_is_saved_after_every_question(self, tmp_path):
        harness = Harness(tmp_path)
        harness.run([question("q1"), question("q2")])
        assert set(harness.store.load()) == {"q1", "q2"}

    def test_finished_questions_are_not_asked_again(self, tmp_path):
        harness = Harness(tmp_path)
        harness.store.append({"id": "q1", "status": "answered", "marker": "from earlier run"})
        rows = harness.run([question("q1"), question("q2")])
        assert harness.searched == ["question q2"]
        assert rows[0]["marker"] == "from earlier run" and rows[1]["id"] == "q2"

    def test_rows_come_back_in_question_order(self, tmp_path):
        rows = Harness(tmp_path).run([question("q2"), question("q1")])
        assert [r["id"] for r in rows] == ["q2", "q1"]


class TestBuildReport:
    def rows(self):
        base = {"answerable": True, "status": "answered", "judged": False, "accuracy": None, "faithfulness": None,
                "source_correct": None, "refusal_correct": True, "latency_ms": 10.0, "llm_calls": 1, "lang": "en"}
        return [
            {**base, "id": "q1", "category": "out_of_scope", "answerable": False},  # no retrieval metrics
            {**base, "id": "q2", "category": "single", "hit@5": 1.0, "mrr": 1.0},
            {**base, "id": "q3", "category": "single", "hit@5": 0.0, "mrr": 0.5},
        ]

    def test_retrieval_means_do_not_depend_on_row_order(self):
        report = build_report(self.rows(), "r4v", "ollama", k=5)
        assert report["retrieval"] == {"hit@5": 0.5, "mrr": 0.75}

    def test_report_names_config_provider_and_models(self):
        report = build_report(self.rows(), "r4v", "groq", k=5)
        assert (report["config"], report["stage"], report["provider"]) == ("r4v", "full", "groq")
        assert report["models"]["answer"] == "openai/gpt-oss-120b"

    def test_breakdowns_by_category_and_language(self):
        report = build_report(self.rows(), "r4v", "ollama", k=5)
        assert report["by_category"]["single"]["n"] == 2 and report["by_category"]["out_of_scope"]["n"] == 1
        assert report["by_lang"]["en"]["n"] == 3

    def test_local_provider_reports_the_local_model_for_every_role(self):
        assert set(build_report(self.rows(), "r0", "ollama", k=5)["models"].values()) == {"llama3.2"}


class TestSummarizeRows:
    def rows(self):
        return [
            {"category": "single", "answerable": True, "status": "answered", "judged": True, "accuracy": 4,
             "faithfulness": 5, "source_correct": True, "refusal_correct": True, "latency_ms": 100.0, "llm_calls": 2},
            {"category": "single", "answerable": True, "status": "answered", "judged": True, "accuracy": 2,
             "faithfulness": 3, "source_correct": False, "refusal_correct": True, "latency_ms": 300.0, "llm_calls": 2},
            {"category": "single", "answerable": True, "status": "not_found", "judged": False, "accuracy": None,
             "faithfulness": None, "source_correct": None, "refusal_correct": False, "latency_ms": 200.0, "llm_calls": 1},
            {"category": "out_of_scope", "answerable": False, "status": "not_found", "judged": False, "accuracy": None,
             "faithfulness": None, "source_correct": None, "refusal_correct": True, "latency_ms": 0.0, "llm_calls": 0},
        ]

    def test_judge_scores_average_only_judged_rows(self):
        summary = summarize_rows(self.rows())
        assert (summary["accuracy"], summary["faithfulness"], summary["n_judged"]) == (3.0, 4.0, 2)

    def test_source_accuracy_ignores_rows_where_it_is_undefined(self):
        assert summarize_rows(self.rows())["source_accuracy"] == 0.5

    def test_refusal_accuracy_counts_every_row(self):
        assert summarize_rows(self.rows())["refusal_accuracy"] == 0.75

    def test_answer_and_refusal_rates_are_split_by_answerability(self):
        summary = summarize_rows(self.rows())
        assert summary["answered_rate"] == pytest.approx(2 / 3)
        assert summary["out_of_scope_refused_rate"] == 1.0

    def test_latency_and_call_counts_are_averaged(self):
        summary = summarize_rows(self.rows())
        assert summary["mean_latency_ms"] == 150.0 and summary["mean_llm_calls"] == 1.25

    def test_undefined_averages_are_none_not_zero(self):
        summary = summarize_rows([self.rows()[3]])
        assert summary["accuracy"] is None and summary["source_accuracy"] is None and summary["answered_rate"] is None

    def test_counts_unjudged_and_broken_replies(self):
        rows = self.rows() + [{**self.rows()[0], "status": "invalid_reply", "judged": False, "accuracy": None}]
        summary = summarize_rows(rows)
        assert summary["n_invalid_reply"] == 1 and summary["n"] == 5
