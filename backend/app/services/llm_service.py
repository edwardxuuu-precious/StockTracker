"""Lightweight LLM client wrapper with provider fallback and JSON parsing helpers."""
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from ..config import get_settings


class LLMUnavailableError(RuntimeError):
    """Raised when LLM cannot be called due to missing config or empty response."""


def _provider_fields() -> tuple[str, str, str, str]:
    settings = get_settings()
    provider = (settings.LLM_PROVIDER or "deepseek").strip().lower()

    if provider == "openrouter":
        api_key = settings.OPENROUTER_API_KEY
        base_url = settings.OPENROUTER_BASE_URL
        model = settings.OPENROUTER_MODEL
    else:
        provider = "deepseek"
        api_key = settings.DEEPSEEK_API_KEY
        base_url = settings.DEEPSEEK_BASE_URL
        model = settings.DEEPSEEK_MODEL
    return provider, api_key, base_url, model


def llm_runtime_info() -> dict[str, Any]:
    """Return current provider settings and whether minimal config is present."""
    provider, api_key, base_url, model = _provider_fields()
    configured = bool(api_key and base_url and model)
    return {
        "provider": provider,
        "base_url": base_url,
        "model": model,
        "configured": configured,
    }


def _provider_config() -> tuple[str, str, str]:
    _, api_key, base_url, model = _provider_fields()

    if not api_key:
        raise LLMUnavailableError("LLM API key is not configured")
    if not base_url or not model:
        raise LLMUnavailableError("LLM base_url/model is not configured")
    return api_key, base_url, model


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise LLMUnavailableError("LLM returned empty content")

    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise LLMUnavailableError("LLM JSON payload not found")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise LLMUnavailableError("LLM JSON payload is not an object")
    return payload


def chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout_seconds: float = 15.0,
) -> str:
    """Call configured LLM provider and return plain text content."""
    api_key, base_url, model = _provider_config()
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise LLMUnavailableError("LLM returned empty content")
    return content


def chat_json(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 1200,
) -> dict[str, Any]:
    """Call configured LLM provider and parse JSON object from response content."""
    text = chat_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return _extract_json_object(text)


def probe_llm_connection(timeout_seconds: float = 8.0) -> tuple[bool, str]:
    """Perform a lightweight online probe against the configured LLM provider."""
    try:
        content = chat_text(
            system_prompt="Reply with one short token: OK",
            user_prompt="health-check",
            temperature=0.0,
            max_tokens=8,
            timeout_seconds=timeout_seconds,
        )
        if content:
            return True, "reachable"
        return False, "empty response"
    except Exception as exc:
        return False, str(exc)
