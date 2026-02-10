"""Security-related configuration tests."""
import pytest

from app.config import DEFAULT_SECRET_KEY, get_settings


def test_default_secret_key_rejected_in_production(monkeypatch: pytest.MonkeyPatch):
    """Production-like environments must not use the placeholder secret."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", DEFAULT_SECRET_KEY)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        get_settings()

    get_settings.cache_clear()


def test_custom_secret_key_allowed_in_production(monkeypatch: pytest.MonkeyPatch):
    """Production-like environments should start with an explicit secret."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "test-production-secret")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.SECRET_KEY == "test-production-secret"

    get_settings.cache_clear()
