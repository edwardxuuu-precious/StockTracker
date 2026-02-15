"""Lightweight LLM client wrapper with provider fallback and JSON parsing helpers."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when LLM cannot be called due to missing config or empty response."""

    def __init__(self, message: str, *, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.metadata = metadata or {}


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


def _provider_config() -> tuple[str, str, str, str]:
    provider, api_key, base_url, model = _provider_fields()

    if not api_key:
        raise LLMUnavailableError("LLM API key is not configured", metadata={"provider": provider})
    if not base_url or not model:
        raise LLMUnavailableError("LLM base_url/model is not configured", metadata={"provider": provider})
    return provider, api_key, base_url, model


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


def _retry_settings(
    timeout_seconds: float | None,
    max_retries: int | None,
) -> tuple[float, int, float, float]:
    settings = get_settings()
    timeout = float(timeout_seconds if timeout_seconds is not None else settings.AGENT_LLM_TIMEOUT_SECONDS)
    retries = int(max_retries if max_retries is not None else settings.AGENT_LLM_MAX_RETRIES)
    base_seconds = float(settings.AGENT_LLM_RETRY_BASE_SECONDS)
    max_seconds = float(settings.AGENT_LLM_RETRY_MAX_SECONDS)
    return max(1.0, timeout), max(0, retries), max(0.0, base_seconds), max(0.0, max_seconds)


def _retry_sleep_seconds(
    *,
    attempt_idx: int,
    base_seconds: float,
    max_seconds: float,
) -> float:
    if base_seconds <= 0:
        return 0.0
    return min(base_seconds * (2 ** attempt_idx), max_seconds) if max_seconds > 0 else base_seconds * (2 ** attempt_idx)


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            LLMUnavailableError,
            BadRequestError,
            AuthenticationError,
            PermissionDeniedError,
            NotFoundError,
            UnprocessableEntityError,
            ConflictError,
        ),
    ):
        return False
    if isinstance(
        exc,
        (
            APITimeoutError,
            APIConnectionError,
            RateLimitError,
            InternalServerError,
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    ):
        return True

    text = str(exc).lower()
    retry_hints = ("timeout", "timed out", "connection", "temporar", "rate limit", "429", "502", "503", "504")
    return any(hint in text for hint in retry_hints)


def _classify_error_type(exc: Exception) -> str:
    if isinstance(exc, (APITimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "network"
    if isinstance(exc, RateLimitError):
        return "rate_limit"
    if isinstance(exc, InternalServerError):
        return "server_error"
    if isinstance(exc, (AuthenticationError, PermissionDeniedError)):
        return "auth"
    if isinstance(exc, (BadRequestError, UnprocessableEntityError, ConflictError, NotFoundError)):
        return "bad_request"
    if isinstance(exc, LLMUnavailableError):
        text = str(exc).lower()
        if "timeout" in text or "timed out" in text:
            return "timeout"
        return "unavailable"

    text = str(exc).lower()
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "rate limit" in text or "429" in text:
        return "rate_limit"
    if "connect" in text or "connection" in text or "network" in text:
        return "network"
    return type(exc).__name__


def _chat_text_with_metadata(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    timeout_seconds: float | None,
    max_retries: int | None,
) -> tuple[str, dict[str, Any]]:
    provider, api_key, base_url, model = _provider_config()
    timeout, retries, base_seconds, max_seconds = _retry_settings(timeout_seconds, max_retries)
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    request_start = time.perf_counter()
    last_error: Exception | None = None
    for attempt_idx in range(retries + 1):
        try:
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
            latency_ms = (time.perf_counter() - request_start) * 1000.0
            metadata = {
                "provider": provider,
                "model": model,
                "latency_ms": latency_ms,
                "retry_count": attempt_idx,
                "timeout_seconds": timeout,
                "error_type": None,
            }
            return content, metadata
        except Exception as exc:  # pragma: no cover - concrete branches validated by unit tests
            last_error = exc
            if attempt_idx >= retries or not _is_retryable_error(exc):
                break
            sleep_seconds = _retry_sleep_seconds(
                attempt_idx=attempt_idx,
                base_seconds=base_seconds,
                max_seconds=max_seconds,
            )
            logger.warning(
                "LLM request failed (attempt %s/%s), retrying in %.2fs: %s",
                attempt_idx + 1,
                retries + 1,
                sleep_seconds,
                exc,
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    attempts = retries + 1
    latency_ms = (time.perf_counter() - request_start) * 1000.0
    error_type = _classify_error_type(last_error or RuntimeError("unknown error"))
    metadata = {
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "retry_count": max(0, attempts - 1),
        "timeout_seconds": timeout,
        "error_type": error_type,
    }
    raise LLMUnavailableError(
        f"LLM request failed after {attempts} attempt(s): {last_error}",
        metadata=metadata,
    ) from last_error


def chat_text_with_metadata(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """Call configured LLM provider and return plain text content with call metadata."""
    return _chat_text_with_metadata(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


def chat_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> str:
    """Call configured LLM provider and return plain text content."""
    content, _metadata = _chat_text_with_metadata(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )
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
            max_retries=0,
        )
        if content:
            return True, "reachable"
        return False, "empty response"
    except Exception as exc:
        return False, str(exc)
