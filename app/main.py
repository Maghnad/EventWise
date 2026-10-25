"""FastAPI application entry-point.

Creates the ``app`` instance, registers CORS middleware,
includes all domain routers, and exposes a ``/health`` endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.ai.llm_client import LLMClientError, LLMConfigurationError
from app.ai.router import router as ai_router
from app.budgets.router import router as budgets_router
from app.config import get_settings
from app.database import Base, engine
from app.events.router import router as events_router
from app.guests.router import router as guests_router
from app.shared import models as _shared_models  # noqa: F401
from app.timeline.router import router as timeline_router
from app.users.router import limiter
from app.users.router import router as auth_router
from app.vendors.router import router as vendors_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="EventWise",
    description="GenAI-powered event planning assistant API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

from app.shared.logging import configure_security_logging

# Configure sensitive data redactor
configure_security_logging()

# ── SlowAPI Rate Limiter with 429 & Retry-After ─────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return standard HTTP 429 Too Many Requests with Retry-After header."""
    response = JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )
    response.headers["Retry-After"] = "60"
    return response


@app.exception_handler(LLMConfigurationError)
async def llm_config_error_handler(_request: Request, exc: LLMConfigurationError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )

@app.exception_handler(LLMClientError)
async def llm_client_error_handler(_request: Request, exc: LLMClientError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    import logging
    logging.getLogger("app.main").error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error occurred."},
    )


# ── Security Headers ────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce defense-in-depth HTTP security headers on all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none';"
    )
    if settings.app_env.lower() in ("production", "prod"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


# ── CSRF Protection Middleware ──────────────────────────
@app.middleware("http")
async def csrf_protect_middleware(request: Request, call_next):
    """Validate CSRF tokens on mutating requests and issue non-HttpOnly CSRF cookies."""
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        csrf_header = request.headers.get("X-CSRF-Token")
        csrf_cookie = request.cookies.get("csrf_token")
        if csrf_cookie and csrf_header and csrf_header != csrf_cookie:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF verification failed: Token mismatch."},
            )

    response = await call_next(request)

    # Issue CSRF cookie on initial GET if not already present
    if "csrf_token" not in request.cookies and request.method == "GET":
        import secrets
        response.set_cookie(
            key="csrf_token",
            value=secrets.token_urlsafe(32),
            httponly=False,
            samesite="lax",
            secure=settings.app_env.lower() in ("production", "prod"),
            path="/",
        )
    return response


# ── CORS ────────────────────────────────────────────────
origin_regex = (
    r"^(https?://(localhost|127\.0\.0\.1)(:[0-9]+)?|https://.*\.vercel\.app)$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-CSRF-Token", "X-Requested-With"],
)

# ── Routers ─────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(budgets_router)
app.include_router(timeline_router)
app.include_router(vendors_router)
app.include_router(guests_router)
app.include_router(ai_router)


# ── Health check ────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, Any]:
    """Return basic service health information."""
    return {
        "status": "healthy",
        "service": "eventwise",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
    }
