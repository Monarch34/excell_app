from __future__ import annotations

import os
import time
import uuid

from fastapi import Request

from src.utils.logger import get_logger

logger = get_logger(__name__)


def is_explicit_cors_configured() -> bool:
    """Return True when CORS_ORIGINS env var is explicitly set."""
    return bool(os.getenv("CORS_ORIGINS", "").strip())


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _is_production_env() -> bool:
    env = (
        (
            os.getenv("APP_ENV")
            or os.getenv("ENV")
            or os.getenv("FASTAPI_ENV")
            or os.getenv("PYTHON_ENV")
            or "development"
        )
        .strip()
        .lower()
    )
    return env in {"prod", "production", "staging"}


def get_allowed_origins() -> list[str]:
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",")]
    if _is_production_env():
        raise RuntimeError("CORS_ORIGINS must be configured in production environments.")
    logger.warning(
        "CORS_ORIGINS not configured - falling back to localhost defaults. "
        "Set CORS_ORIGINS env var for production use."
    )
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]


async def request_id_middleware(request: Request, call_next):
    started_at = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "%s %s -> %s (%.1fms) [request_id=%s]",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response


async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if _env_flag("ENABLE_SECURITY_CSP", True):
        response.headers["Content-Security-Policy"] = os.getenv(
            "CONTENT_SECURITY_POLICY",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none';",
        )
    if _env_flag("ENABLE_HSTS", True):
        response.headers["Strict-Transport-Security"] = os.getenv(
            "STRICT_TRANSPORT_SECURITY",
            "max-age=31536000; includeSubDomains",
        )
    if _env_flag("ENABLE_PERMISSIONS_POLICY", True):
        response.headers["Permissions-Policy"] = os.getenv(
            "PERMISSIONS_POLICY",
            "geolocation=(), camera=(), microphone=()",
        )
    return response
