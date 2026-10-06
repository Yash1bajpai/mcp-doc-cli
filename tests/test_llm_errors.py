import httpx
import openai
import pytest

from core.claude import Claude, LLMError


def _err(cls, status):
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    return cls("x", response=httpx.Response(status, request=req), body=None)


def _claude(exc, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    c = Claude(model="m/free")
    def boom(**_):
        raise exc
    monkeypatch.setattr(c.client.chat.completions, "create", boom)
    monkeypatch.setattr("time.sleep", lambda _: None)
    return c


def test_404_is_friendly(monkeypatch):
    c = _claude(_err(openai.NotFoundError, 404), monkeypatch)
    with pytest.raises(LLMError, match="no longer available"):
        c.chat([{"role": "user", "content": "hi"}])


def test_429_is_friendly_after_retries(monkeypatch):
    c = _claude(_err(openai.RateLimitError, 429), monkeypatch)
    with pytest.raises(LLMError, match="rate limited"):
        c.chat([{"role": "user", "content": "hi"}])


def test_401_is_friendly(monkeypatch):
    c = _claude(_err(openai.AuthenticationError, 401), monkeypatch)
    with pytest.raises(LLMError, match="API key"):
        c.chat([{"role": "user", "content": "hi"}])


def test_429_retries_exactly_three_times(monkeypatch):
    c = _claude(_err(openai.RateLimitError, 429), monkeypatch)
    attempts = []

    def boom(**_):
        attempts.append(1)
        raise _err(openai.RateLimitError, 429)

    monkeypatch.setattr(c.client.chat.completions, "create", boom)
    with pytest.raises(LLMError):
        c.chat([{"role": "user", "content": "hi"}])
    assert len(attempts) == 3


def test_cli_prints_error_and_continues(capsys):
    import asyncio
    from types import SimpleNamespace
    from core.cli import CliApp

    inputs = iter(["first", "second"])
    calls = []

    async def prompt_async(_):
        try:
            return next(inputs)
        except StopIteration:
            raise KeyboardInterrupt

    async def run(text):
        calls.append(text)
        if text == "first":
            raise LLMError("rate limited test")
        return "recovered"

    app = object.__new__(CliApp)
    app.session = SimpleNamespace(prompt_async=prompt_async)
    app.agent = SimpleNamespace(run=run)
    asyncio.run(app.run())
    output = capsys.readouterr().out
    assert "Error: rate limited test" in output
    assert "Response:\nrecovered" in output
    assert calls == ["first", "second"]
