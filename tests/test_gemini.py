import numpy as np
import pytest

from rag.gemini import DailyQuotaExceeded, embed_in_batches, is_retryable, retry_delay


class ApiError(Exception):
    def __init__(self, code: int, message: str = ""):
        super().__init__(message or f"api error {code}")
        self.code = code


def echo_call(batch: list[str]) -> np.ndarray:
    return np.array([[float(len(t)), 1.0] for t in batch], dtype=np.float32)


class Recorder:
    def __init__(self):
        self.sleeps: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.sleeps.append(seconds)


class TestIsRetryable:
    @pytest.mark.parametrize("code", [429, 500, 503, 504])
    def test_rate_limit_and_server_errors_are_retryable(self, code):
        assert is_retryable(ApiError(code))

    @pytest.mark.parametrize("error", [ApiError(400), ApiError(403), ValueError("x")])
    def test_client_errors_and_unknown_errors_are_not(self, error):
        assert not is_retryable(error)


class TestBatching:
    def test_splits_into_batches_and_keeps_order(self):
        calls = []

        def call(batch):
            calls.append(list(batch))
            return echo_call(batch)

        out = embed_in_batches(call, ["a", "bb", "ccc", "dddd", "e"], batch_size=2, sleep=Recorder())
        assert calls == [["a", "bb"], ["ccc", "dddd"], ["e"]]
        assert out[:, 0].tolist() == [1.0, 2.0, 3.0, 4.0, 1.0]

    def test_waits_between_requests_but_not_after_the_last(self):
        sleep = Recorder()
        embed_in_batches(echo_call, ["a", "b", "c"], batch_size=1, texts_per_minute=30, sleep=sleep)
        assert sleep.sleeps == [2.0, 2.0]

    def test_wait_scales_with_batch_size_to_stay_under_the_per_minute_limit(self):
        sleep = Recorder()
        embed_in_batches(echo_call, ["a"] * 4, batch_size=2, texts_per_minute=60, sleep=sleep)
        assert sleep.sleeps == [2.0]  # 2 texts at 60/min = 2 seconds

    def test_wrong_number_of_vectors_is_an_error(self):
        with pytest.raises(ValueError, match="1.*2"):
            embed_in_batches(lambda batch: np.zeros((1, 2)), ["a", "b"], batch_size=2, sleep=Recorder())


class TestRetry:
    def flaky(self, failures: int, code: int = 429):
        state = {"left": failures}

        def call(batch):
            if state["left"] > 0:
                state["left"] -= 1
                raise ApiError(code)
            return echo_call(batch)

        return call

    def test_retries_a_retryable_error_then_succeeds(self):
        sleep = Recorder()
        out = embed_in_batches(self.flaky(2), ["a"], batch_size=1, sleep=sleep)
        assert out.shape == (1, 2)
        assert len(sleep.sleeps) == 2

    def test_backoff_grows_between_attempts(self):
        sleep = Recorder()
        embed_in_batches(self.flaky(3), ["a"], batch_size=1, sleep=sleep)
        assert sleep.sleeps == sorted(sleep.sleeps) and sleep.sleeps[0] < sleep.sleeps[-1]

    def test_waits_as_long_as_the_server_asks(self):
        sleep = Recorder()
        state = {"failed": False}

        def call(batch):
            if not state["failed"]:
                state["failed"] = True
                raise ApiError(429, "quota exceeded. Please retry in 57.44s.")
            return echo_call(batch)

        embed_in_batches(call, ["a"], batch_size=1, sleep=sleep)
        assert sleep.sleeps == [pytest.approx(58.44)]

    def test_server_hint_is_capped(self):
        assert retry_delay(ApiError(429, "Please retry in 9999s"), attempt=0) == 120.0

    def test_daily_quota_stops_at_once_instead_of_waiting_for_hours(self):
        sleep = Recorder()
        daily = ApiError(429, "Embed content requests per day limit exceeded. Please retry in 19h52m30s")
        with pytest.raises(DailyQuotaExceeded, match="resume"):
            embed_in_batches(lambda batch: (_ for _ in ()).throw(daily), ["a"], batch_size=1, sleep=sleep)
        assert sleep.sleeps == []

    def test_per_minute_quota_is_still_retried(self):
        sleep = Recorder()
        out = embed_in_batches(
            self.flaky_with("requests per minute limit exceeded. Please retry in 5s"), ["a"], batch_size=1, sleep=sleep
        )
        assert out.shape == (1, 2) and len(sleep.sleeps) == 1

    def flaky_with(self, message: str):
        state = {"failed": False}

        def call(batch):
            if not state["failed"]:
                state["failed"] = True
                raise ApiError(429, message)
            return echo_call(batch)

        return call

    def test_gives_up_after_max_retries(self):
        with pytest.raises(ApiError):
            embed_in_batches(self.flaky(10), ["a"], batch_size=1, max_retries=2, sleep=Recorder())

    def test_non_retryable_error_is_raised_immediately(self):
        sleep = Recorder()
        with pytest.raises(ApiError):
            embed_in_batches(self.flaky(1, code=400), ["a"], batch_size=1, sleep=sleep)
        assert sleep.sleeps == []
