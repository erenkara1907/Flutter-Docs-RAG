from types import SimpleNamespace

import httpx
import openai
import pytest

from rag.llm import DailyQuotaExceeded, groq_stream


def piece(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def client_playing(items=(), error=None, calls=None):
    def create(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        if error:
            raise error
        return iter(items)

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def rate_limit(message):
    response = httpx.Response(429, request=httpx.Request("POST", "http://groq.test"))
    return openai.RateLimitError(message, response=response, body=None)


class TestGroqStream:
    def test_json_mode_is_off_because_groq_then_sends_the_whole_reply_in_one_piece(self):
        calls = []
        list(groq_stream("m", client=client_playing([], calls=calls))("hello"))
        assert "response_format" not in calls[0]

    def test_yields_the_text_pieces_in_order(self):
        stream = groq_stream("m", client=client_playing([piece('{"ans'), piece('wer"'), piece(": 1}")]))
        assert list(stream("prompt")) == ['{"ans', 'wer"', ": 1}"]

    def test_skips_pieces_without_text(self):
        empty_choices = SimpleNamespace(choices=[])
        stream = groq_stream("m", client=client_playing([piece("a"), piece(None), empty_choices, piece("")]))
        assert list(stream("p")) == ["a"]

    def test_asks_for_a_streamed_reply_from_the_given_model(self):
        calls = []
        list(groq_stream("openai/x", seed=7, client=client_playing([], calls=calls))("hello"))
        sent = calls[0]
        assert sent["model"] == "openai/x" and sent["stream"] is True and sent["seed"] == 7
        assert sent["messages"] == [{"role": "user", "content": "hello"}]

    def test_a_daily_quota_error_becomes_daily_quota_exceeded(self):
        error = rate_limit("Rate limit reached ... tokens per day (TPD): Limit 200000")
        with pytest.raises(DailyQuotaExceeded):
            list(groq_stream("m", client=client_playing(error=error))("p"))

    def test_other_rate_limits_are_passed_on(self):
        error = rate_limit("Rate limit reached ... tokens per minute (TPM)")
        with pytest.raises(openai.RateLimitError):
            list(groq_stream("m", client=client_playing(error=error))("p"))
