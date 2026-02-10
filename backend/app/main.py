"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import init_db
from .api.v1 import portfolio
from .api.v1 import holding
from .api.v1 import telemetry
from .api.v1 import quotes
from .api.v1 import analytics
from .api.v1 import strategy
from .api.v1 import backtest
from .api.v1 import market_data
from .api.v1 import knowledge_base
from .api.v1 import agent
from .api.v1 import chat

settings = get_settings()


def _safe_log(message: str) -> None:
    """Best-effort stdout logging that never breaks request handling."""
    try:
        print(message, flush=True)
    except Exception:
        # Ignore logging sink failures (detached stdout, broken pipe, etc.).
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize resources on startup and keep teardown hook available."""
    init_db()
    _safe_log("[OK] Database initialized")
    yield


# Create FastAPI application
app = FastAPI(
    title="StockTracker API",
    description="AI-powered stock portfolio and trading strategy management system",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS via settings to avoid accidental wildcard exposure.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log each request with timing info to stdout for easy tracing in the server window.
# Do not log request bodies to avoid leaking credentials/tokens in logs.
class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        client_host = request.client.host if request.client else "unknown"
        query_suffix = "?..." if request.url.query else ""
        _safe_log(
            f"[REQ {request_id}] {request.method} {request.url.path}{query_suffix} "
            f"(from {client_host})"
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            _safe_log(
                f"[REQ {request_id}] {request.method} {request.url.path} "
                f"-> 500 ERROR {duration_ms:.1f}ms ({type(exc).__name__})"
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        size = response.headers.get("content-length", "-")
        _safe_log(
            f"[REQ {request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} {duration_ms:.1f}ms size={size}"
        )
        return response

# Add request logger middleware early so every request is captured.
app.add_middleware(RequestLogMiddleware)

# API Routes
@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "StockTracker API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Include routers
app.include_router(portfolio.router, prefix="/api/v1/portfolios", tags=["portfolios"])
app.include_router(holding.router, prefix="/api/v1/portfolios", tags=["holdings"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["quotes"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(strategy.router, prefix="/api/v1/strategies", tags=["strategies"])
app.include_router(backtest.router, prefix="/api/v1/backtests", tags=["backtests"])
app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["market-data"])
app.include_router(knowledge_base.router, prefix="/api/v1/kb", tags=["knowledge-base"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# Additional routers will be added in later phases
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(stock.router, prefix="/api/v1/stocks", tags=["stocks"])
# app.include_router(strategy.router, prefix="/api/v1/strategies", tags=["strategies"])
# app.include_router(backtest.router, prefix="/api/v1/backtests", tags=["backtests"])
# app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True if settings.APP_ENV == "development" else False,
    )
