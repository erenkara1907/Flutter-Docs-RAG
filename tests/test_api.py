import pytest
from fastapi.testclient import TestClient

from main import SlidingWindowLimiter, create_app
from rag.answer import Answer, Source
from rag.llm import DailyQuotaExceeded

SOURCE = Source(title="Layout", url="https://docs.flutter.dev/ui/layout")


def good_answer(question: str) -> Answer:
    return Answer(answer=f"echo: {question}", status="answered", sources=[SOURCE])


def client(answer_fn=good_answer, limit=100) -> TestClient:
    return TestClient(create_app(answer_fn, SlidingWindowLimiter(limit, 60.0)))


class TestAsk:
    def test_returns_the_answer_with_its_sources(self):
        response = client().post("/api/ask", json={"question": "How do I use Row?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "echo: How do I use Row?" and body["status"] == "answered"
        assert body["sources"] == [{"title": "Layout", "url": "https://docs.flutter.dev/ui/layout"}]

    @pytest.mark.parametrize("question", ["", "   ", "x" * 301])
    def test_empty_or_too_long_questions_are_a_400_and_never_reach_the_model(self, question):
        def must_not_run(q):
            raise AssertionError("the model must not be called")

        response = client(must_not_run).post("/api/ask", json={"question": question})
        assert response.status_code == 400

    def test_a_question_of_exactly_300_characters_is_accepted(self):
        assert client().post("/api/ask", json={"question": "x" * 300}).status_code == 200

    def test_a_body_without_a_question_is_rejected(self):
        assert client().post("/api/ask", json={}).status_code == 422

    def test_a_non_string_question_is_rejected(self):
        assert client().post("/api/ask", json={"question": ["a"]}).status_code == 422


class TestFailures:
    def test_an_exhausted_model_quota_is_a_503_with_a_plain_message(self):
        def quota(q):
            raise DailyQuotaExceeded("daily limit")

        response = client(quota).post("/api/ask", json={"question": "hello"})
        assert response.status_code == 503
        assert "daily limit" not in response.text

    def test_unexpected_errors_do_not_leak_details(self):
        def broken(q):
            raise RuntimeError("secret internal detail gsk_123")

        response = client(broken).post("/api/ask", json={"question": "hello"})
        assert response.status_code == 503
        assert "gsk_123" not in response.text and "secret" not in response.text


class TestRateLimit:
    def test_requests_over_the_limit_get_429(self):
        c = client(limit=2)
        codes = [c.post("/api/ask", json={"question": "hello"}).status_code for _ in range(3)]
        assert codes == [200, 200, 429]

    def test_rejected_questions_count_too(self):
        c = client(limit=1)
        c.post("/api/ask", json={"question": ""})
        assert c.post("/api/ask", json={"question": "hello"}).status_code == 429


class TestLimiter:
    def test_window_slides(self):
        now = [0.0]
        limiter = SlidingWindowLimiter(2, 10.0, clock=lambda: now[0])
        assert [limiter.allow("a"), limiter.allow("a"), limiter.allow("a")] == [True, True, False]
        now[0] = 10.1
        assert limiter.allow("a") is True

    def test_clients_are_counted_separately(self):
        limiter = SlidingWindowLimiter(1, 10.0)
        assert limiter.allow("a") is True and limiter.allow("b") is True

    def test_idle_clients_are_forgotten(self):
        now = [0.0]
        limiter = SlidingWindowLimiter(1, 10.0, clock=lambda: now[0])
        limiter.allow("a")
        now[0] = 100.0
        limiter.allow("b")
        assert "a" not in limiter.known_clients()


class TestStaticMount:
    def test_local_runs_serve_the_page_but_vercel_leaves_it_to_its_cdn(self):
        from main import should_serve_static

        assert should_serve_static({}) is True
        assert should_serve_static({"VERCEL": "1"}) is False


class TestForwardedClient:
    def test_the_first_forwarded_address_is_the_client(self):
        c = client(limit=1)
        assert c.post("/api/ask", json={"question": "hi"}, headers={"x-forwarded-for": "1.1.1.1, 9.9.9.9"}).status_code == 200
        assert c.post("/api/ask", json={"question": "hi"}, headers={"x-forwarded-for": "2.2.2.2"}).status_code == 200
        assert c.post("/api/ask", json={"question": "hi"}, headers={"x-forwarded-for": "1.1.1.1"}).status_code == 429
