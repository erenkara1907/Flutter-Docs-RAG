import json

import pytest

from eval.golden import GoldenQuestion
from eval.run import Retrieval, evaluate, mean_metrics, retrieval_llm, score_question, write_report
from rag.config import RunConfig

URL_A = "https://docs.flutter.dev/a"
URL_B = "https://docs.flutter.dev/b"
URL_C = "https://docs.flutter.dev/c"


def make_question(qid="q001", category="single", lang="en", urls=(URL_A,), answerable=True):
    return GoldenQuestion(
        id=qid, category=category, lang=lang, question=f"question {qid}",
        expected_urls=list(urls), reference_answer="answer", answerable=answerable,
    )


def out_of_scope(qid="q900"):
    return make_question(qid, category="out_of_scope", urls=(), answerable=False)


class TestRetrievalLlm:
    def test_configs_without_llm_steps_get_none(self):
        assert retrieval_llm(RunConfig(name="x"), "groq") is None

    def test_the_default_provider_leaves_the_choice_to_the_pipeline(self):
        assert retrieval_llm(RunConfig(name="x", rewrite=True), "ollama") is None

    def test_groq_is_built_for_rewrite_and_rerank_configs(self, monkeypatch):
        calls = []
        monkeypatch.setattr("eval.run.make_llm", lambda role, provider, seed: calls.append((role, provider, seed)) or "llm")
        assert retrieval_llm(RunConfig(name="x", rewrite=True), "groq") == "llm"
        assert calls == [("rewrite", "groq", 42)]


class TestScoreQuestion:
    def test_duplicate_pages_are_collapsed_before_scoring(self):
        # chunks come from pages A, A, B: page B is rank 2, not rank 3
        scores = score_question(make_question(urls=(URL_B,)), [URL_A, URL_A, URL_B], k=5)
        assert scores["mrr"] == 0.5

    def test_returns_all_four_metrics(self):
        scores = score_question(make_question(), [URL_A], k=5)
        assert scores == {"hit@5": 1.0, "recall@5": 1.0, "mrr": 1.0, "ndcg@5": 1.0}

    def test_k_is_part_of_the_metric_names(self):
        assert "hit@3" in score_question(make_question(), [URL_A], k=3)


class TestMeanMetrics:
    def test_averages_each_metric(self):
        rows = [{"mrr": 1.0, "hit@5": 1.0}, {"mrr": 0.0, "hit@5": 1.0}]
        assert mean_metrics(rows) == {"mrr": 0.5, "hit@5": 1.0}

    def test_empty_rows_give_empty_dict(self):
        assert mean_metrics([]) == {}


def fake_retriever(question):
    urls = {
        "question q001": [URL_A],
        "question q002": [URL_C],
        "question q071": [URL_A],
    }[question]
    return Retrieval(urls=urls, search_query=f"rewritten {question}")


def sample_questions():
    return [
        make_question("q001", urls=(URL_A,)),
        make_question("q002", urls=(URL_B,)),
        make_question("q071", category="tr", lang="tr", urls=(URL_A,)),
        out_of_scope(),
    ]


class TestEvaluate:
    def run(self):
        return evaluate(sample_questions(), fake_retriever, k=5)

    def test_out_of_scope_is_skipped_and_counted(self):
        report = self.run()
        assert report["n_scored"] == 3
        assert report["n_skipped_out_of_scope"] == 1

    def test_overall_mean(self):
        assert self.run()["overall"]["mrr"] == pytest.approx(2 / 3)

    def test_breakdown_by_category(self):
        by_category = self.run()["by_category"]
        assert by_category["single"]["mrr"] == 0.5
        assert by_category["single"]["n"] == 2
        assert by_category["tr"]["mrr"] == 1.0
        assert "out_of_scope" not in by_category

    def test_breakdown_by_language(self):
        by_lang = self.run()["by_lang"]
        assert by_lang["en"]["n"] == 2
        assert by_lang["tr"]["mrr"] == 1.0

    def test_per_question_rows_keep_retrieved_urls_for_error_analysis(self):
        rows = {r["id"]: r for r in self.run()["per_question"]}
        assert rows["q002"]["retrieved_urls"] == [URL_C]
        assert rows["q002"]["expected_urls"] == [URL_B]
        assert rows["q002"]["mrr"] == 0.0

    def test_rewritten_query_is_recorded_for_error_analysis(self):
        rows = {r["id"]: r for r in self.run()["per_question"]}
        assert rows["q002"]["search_query"] == "rewritten question q002"

    def test_search_query_is_omitted_when_the_retriever_did_not_rewrite(self):
        report = evaluate([make_question()], lambda q: Retrieval(urls=[URL_A]), k=5)
        assert "search_query" not in report["per_question"][0]

    def test_every_question_records_its_latency(self):
        report = self.run()
        assert all(row["latency_ms"] >= 0 for row in report["per_question"])
        assert report["mean_latency_ms"] >= 0

    def test_no_scorable_questions_is_an_error(self):
        with pytest.raises(ValueError, match="no scorable"):
            evaluate([out_of_scope()], lambda q: Retrieval(urls=[]), k=5)


def test_write_report_creates_parent_dirs_and_valid_json(tmp_path):
    path = tmp_path / "results" / "r0-retrieval.json"
    write_report({"overall": {"mrr": 0.5}}, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {"overall": {"mrr": 0.5}}
