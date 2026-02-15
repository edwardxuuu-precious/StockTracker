"""Unit tests for LLM timeout and retry behavior."""

import pytest


def test_chat_text_retries_and_succeeds(monkeypatch):
    from app.config import get_settings
    from app.services import llm_service

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("AGENT_LLM_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    state = {"calls": 0}

    class _FakeCompletions:
        def create(self, **kwargs):
            state["calls"] += 1
            if state["calls"] < 3:
                raise TimeoutError("request timed out")
            return type(
                "Resp",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {"message": type("Msg", (), {"content": "OK"})()},
                        )()
                    ]
                },
            )()

    class _FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": _FakeCompletions()})()

    monkeypatch.setattr(llm_service, "OpenAI", _FakeClient)
    monkeypatch.setattr(llm_service.time, "sleep", lambda _seconds: None)

    try:
        content = llm_service.chat_text(
            system_prompt="system",
            user_prompt="user",
        )
    finally:
        get_settings.cache_clear()

    assert content == "OK"
    assert state["calls"] == 3


def test_chat_text_non_retryable_error_fails_fast(monkeypatch):
    from app.config import get_settings
    from app.services import llm_service

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("AGENT_LLM_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    state = {"calls": 0}

    class _FakeCompletions:
        def create(self, **kwargs):
            state["calls"] += 1
            raise ValueError("bad request payload")

    class _FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": _FakeCompletions()})()

    monkeypatch.setattr(llm_service, "OpenAI", _FakeClient)
    monkeypatch.setattr(llm_service.time, "sleep", lambda _seconds: None)

    try:
        with pytest.raises(llm_service.LLMUnavailableError, match="attempt\\(s\\)"):
            llm_service.chat_text(system_prompt="system", user_prompt="user")
    finally:
        get_settings.cache_clear()

    assert state["calls"] == 1


def test_chat_text_with_metadata_contains_latency_and_retry(monkeypatch):
    from app.config import get_settings
    from app.services import llm_service

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("AGENT_LLM_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    class _FakeCompletions:
        def create(self, **kwargs):
            return type(
                "Resp",
                (),
                {
                    "choices": [
                        type(
                            "Choice",
                            (),
                            {"message": type("Msg", (), {"content": "OK"})()},
                        )()
                    ]
                },
            )()

    class _FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": _FakeCompletions()})()

    monkeypatch.setattr(llm_service, "OpenAI", _FakeClient)
    try:
        content, metadata = llm_service.chat_text_with_metadata(
            system_prompt="system",
            user_prompt="user",
        )
    finally:
        get_settings.cache_clear()

    assert content == "OK"
    assert metadata["provider"] == "deepseek"
    assert metadata["retry_count"] == 0
    assert metadata["error_type"] is None
    assert metadata["latency_ms"] >= 0


def test_chat_text_timeout_failure_exposes_timeout_error_type(monkeypatch):
    from app.config import get_settings
    from app.services import llm_service

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("AGENT_LLM_MAX_RETRIES", "1")
    monkeypatch.setenv("AGENT_LLM_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()

    class _FakeCompletions:
        def create(self, **kwargs):
            raise TimeoutError("request timed out")

    class _FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("Chat", (), {"completions": _FakeCompletions()})()

    monkeypatch.setattr(llm_service, "OpenAI", _FakeClient)
    monkeypatch.setattr(llm_service.time, "sleep", lambda _seconds: None)
    try:
        with pytest.raises(llm_service.LLMUnavailableError) as exc_info:
            llm_service.chat_text(system_prompt="system", user_prompt="user")
    finally:
        get_settings.cache_clear()

    metadata = exc_info.value.metadata
    assert metadata["error_type"] == "timeout"
    assert metadata["retry_count"] == 1
