"""Application configuration management."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "your-secret-key-change-this-in-production"

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

    # Stock Data Providers
    TUSHARE_TOKEN: str = ""
    YFINANCE_TIMEOUT: int = 10

    # Cache Settings
    CACHE_QUOTE_TTL: int = 60  # seconds
    CACHE_HISTORY_TTL: int = 3600  # seconds

    # Real-time Tracking
    REALTIME_UPDATE_INTERVAL: int = 60  # seconds
    ENABLE_WEBSOCKET: bool = False

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
