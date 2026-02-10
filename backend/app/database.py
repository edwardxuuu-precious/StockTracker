"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Ensure all SQLAlchemy models are registered before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema_compatibility()
    try:
        from .services.knowledge_base import ensure_kb_schema
    except Exception:
        return
    ensure_kb_schema(engine)


def _ensure_runtime_schema_compatibility() -> None:
    """Apply lightweight SQLite schema patches for backward compatibility."""
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(backtests)")).fetchall()
        if not columns:
            return
        names = {str(row[1]) for row in columns}
        if "strategy_version_id" not in names:
            conn.execute(text("ALTER TABLE backtests ADD COLUMN strategy_version_id INTEGER"))
