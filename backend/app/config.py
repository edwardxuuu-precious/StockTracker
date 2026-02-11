"""Application configuration management."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

DEFAULT_SECRET_KEY = "your-secret-key-change-this-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = DEFAULT_SECRET_KEY

    # Database
    DATABASE_URL: str = "sqlite:///./stocktracker.db"

    # LLM Configuration
    LLM_PROVIDER: str = "deepseek"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # OpenRouter (backup/testing)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    AGENT_REQUIRE_LLM: bool = True
    AGENT_STARTUP_CHECK_LLM: bool = True
    AGENT_STARTUP_PROBE_LLM: bool = True
    AGENT_STARTUP_LLM_TIMEOUT_SECONDS: float = 8.0

    # Stock Data Providers
    TUSHARE_TOKEN: str = ""
    YFINANCE_TIMEOUT: int = 10

    # Cache Settings
    CACHE_QUOTE_TTL: int = 60  # seconds
    CACHE_HISTORY_TTL: int = 3600  # seconds

    # Knowledge base retrieval governance
    KB_MIN_SCORE: float = 0.08
    KB_MAX_PER_DOCUMENT: int = 2
    KB_ALLOW_FALLBACK_CITATIONS: bool = True
    KB_ALLOWED_SOURCE_TYPES: list[str] = ["pdf", "txt", "text", "json"]
    KB_BLOCKED_SOURCE_KEYWORDS: list[str] = []
    KB_PREFERRED_SOURCE_TYPES: list[str] = ["pdf", "txt", "text", "json"]
    KB_RECENCY_HALF_LIFE_DAYS: int = 180
    KB_POLICY_PROFILE: str = "balanced"

    # Real-time Tracking
    REALTIME_UPDATE_INTERVAL: int = 60  # seconds
    ENABLE_WEBSOCKET: bool = False
    # Backtest mode
    ALLOW_SIM_BACKTEST: bool = False

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    env = settings.APP_ENV.lower()
    non_prod_envs = {"development", "dev", "local", "test", "testing"}
    if env not in non_prod_envs and settings.SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY must be explicitly set when APP_ENV is not development/test."
        )
    return settings
