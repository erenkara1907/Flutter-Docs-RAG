import pytest

from rag.llm import (
    GROQ_MODELS,
    DailyQuotaExceeded,
    estimate_tokens,
    is_daily_quota,
    parse_duration,
    parse_json_object,
    retry_wait,
    seconds_to_wait,
)


class TestParseJsonObject:
    def test_plain_object(self):
        assert parse_json_object('{"a": 1}') == {"a": 1}

    def test_markdown_fence_is_removed(self):
        assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}

    @pytest.mark.parametrize("raw", ["nope", "[1]", '"text"', ""])
    def test_anything_else_is_a_value_error(self, raw):
        with pytest.raises(ValueError):
            parse_json_object(raw)


class TestParseDuration:
    @pytest.mark.parametrize(
        ("text", "seconds"),
        [("7.66s", 7.66), ("1m30s", 90.0), ("1m30.5s", 90.5), ("250ms", 0.25), ("2m", 120.0), ("1h2m", 3720.0), ("0s", 0.0)],
    )
    def test_groq_style_durations(self, text, seconds):
        assert parse_duration(text) == pytest.approx(seconds)

    @pytest.mark.parametrize("text", ["", "soon", None])
    def test_unparseable_gives_none(self, text):
        assert parse_duration(text) is None


class TestSecondsToWait:
    def test_unknown_quota_means_no_wait(self):
        assert seconds_to_wait(remaining_tokens=None, reset_s=None, needed=3000) == 0.0

    def test_enough_tokens_left_means_no_wait(self):
        assert seconds_to_wait(remaining_tokens=5000, reset_s=40.0, needed=3000) == 0.0

    def test_too_few_tokens_waits_for_the_reset_plus_a_margin(self):
        assert seconds_to_wait(remaining_tokens=1000, reset_s=12.0, needed=3000) == pytest.approx(12.5)

    def test_unknown_reset_assumes_a_full_minute(self):
        assert seconds_to_wait(remaining_tokens=0, reset_s=None, needed=10) == pytest.approx(60.5)


class TestEstimateTokens:
    def test_grows_with_prompt_and_with_requested_output(self):
        assert estimate_tokens("a" * 3000, max_tokens=500) > estimate_tokens("a" * 300, max_tokens=500)
        assert estimate_tokens("a" * 300, max_tokens=1000) > estimate_tokens("a" * 300, max_tokens=500)


class TestRetryWait:
    def test_reads_the_hint_from_the_error_message(self):
        message = "Rate limit reached ... on tokens per minute (TPM): Limit 8000. Please try again in 7.66s."
        assert retry_wait(message) == pytest.approx(8.16)

    def test_minutes_and_seconds(self):
        assert retry_wait("Please try again in 1m30s.") == pytest.approx(90.5)

    def test_without_a_hint_waits_a_default(self):
        assert retry_wait("something else went wrong") == 20.0


class TestDailyQuota:
    def test_per_day_limits_are_detected(self):
        assert is_daily_quota("Rate limit reached on tokens per day (TPD): Limit 200000")
        assert is_daily_quota("... requests per day (RPD) ...")

    def test_per_minute_limits_are_not_daily(self):
        assert not is_daily_quota("Rate limit reached on tokens per minute (TPM)")

    def test_exception_message_mentions_resuming(self):
        assert "resume" in str(DailyQuotaExceeded("Groq daily quota used up; resume tomorrow"))


def test_every_role_has_a_groq_model():
    assert set(GROQ_MODELS) == {"rewrite", "rerank", "answer", "judge"}


def test_judge_is_a_different_model_family_from_the_answerer():
    assert GROQ_MODELS["judge"].split("/")[0] != GROQ_MODELS["answer"].split("/")[0]
