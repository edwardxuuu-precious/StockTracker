"""Main FastAPI application entry point."""
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

# Create FastAPI application
app = FastAPI(
    title="StockTracker API",
    description="AI-powered stock portfolio and trading strategy management system",
    version="1.0.0",
)

# Configure CORS - Allow all origins temporarily
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

# Log each request with timing info to stdout for easy tracing in the server window.
class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        client_host = request.client.host if request.client else "unknown"
        query = f"?{request.url.query}" if request.url.query else ""
        body_preview = ""
        content_type = request.headers.get("content-type", "")
        should_log_body = request.method in ("POST", "PUT", "PATCH") or content_type.startswith("application/json")
        if should_log_body:
            try:
                raw_body = await request.body()
                if raw_body:
                    max_len = 2048
                    text = raw_body[:max_len].decode("utf-8", errors="replace")
                    if len(raw_body) > max_len:
                        text += "...(truncated)"
                    body_preview = f" body={text}"
            except Exception:
                body_preview = " body=<unavailable>"

        print(
            f"[REQ {request_id}] {request.method} {request.url.path}{query} "
            f"(from {client_host}){body_preview}",
            flush=True,
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            print(
                f"[REQ {request_id}] {request.method} {request.url.path} "
                f"-> 500 ERROR {duration_ms:.1f}ms ({type(exc).__name__})",
                flush=True,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        size = response.headers.get("content-length", "-")
        print(
            f"[REQ {request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} {duration_ms:.1f}ms size={size}",
            flush=True,
        )
        return response

# Add request logger middleware early so every request is captured.
app.add_middleware(RequestLogMiddleware)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    init_db()
    print("[OK] Database initialized", flush=True)


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
