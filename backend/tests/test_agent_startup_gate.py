"""Tests for strict agent LLM startup gate."""

import pytest


def _set_env(monkeypatch, **kwargs):
    for key, value in kwargs.items():
        monkeypatch.setenv(key, str(value))


def test_startup_gate_skips_when_not_required(monkeypatch):
    from app.config import get_settings
    from app import main as app_main

    _set_env(
        monkeypatch,
        AGENT_REQUIRE_LLM="false",
        AGENT_STARTUP_CHECK_LLM="true",
    )
    get_settings.cache_clear()
    try:
        app_main._validate_agent_llm_readiness()
    finally:
        get_settings.cache_clear()


def test_startup_gate_fails_when_required_but_unconfigured(monkeypatch):
    from app.config import get_settings
    from app import main as app_main

    _set_env(
        monkeypatch,
        AGENT_REQUIRE_LLM="true",
        AGENT_STARTUP_CHECK_LLM="true",
        AGENT_STARTUP_PROBE_LLM="false",
        DEEPSEEK_API_KEY="",
    )
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="provider config is missing"):
            app_main._validate_agent_llm_readiness()
    finally:
        get_settings.cache_clear()


def test_startup_gate_fails_on_probe_error(monkeypatch):
    from app.config import get_settings
    from app import main as app_main

    _set_env(
        monkeypatch,
        AGENT_REQUIRE_LLM="true",
        AGENT_STARTUP_CHECK_LLM="true",
        AGENT_STARTUP_PROBE_LLM="true",
        DEEPSEEK_API_KEY="test-key",
    )
    monkeypatch.setattr(app_main, "probe_llm_connection", lambda timeout_seconds=8.0: (False, "timeout"))
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="probe failed"):
            app_main._validate_agent_llm_readiness()
    finally:
        get_settings.cache_clear()


def test_startup_gate_passes_on_successful_probe(monkeypatch):
    from app.config import get_settings
    from app import main as app_main

    _set_env(
        monkeypatch,
        AGENT_REQUIRE_LLM="true",
        AGENT_STARTUP_CHECK_LLM="true",
        AGENT_STARTUP_PROBE_LLM="true",
        DEEPSEEK_API_KEY="test-key",
    )
    monkeypatch.setattr(app_main, "probe_llm_connection", lambda timeout_seconds=8.0: (True, "reachable"))
    get_settings.cache_clear()
    try:
        app_main._validate_agent_llm_readiness()
    finally:
        get_settings.cache_clear()
