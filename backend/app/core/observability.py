from __future__ import annotations

import json
import logging
import re
import sys
import time
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any, TextIO
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings

REQUEST_ID_HEADER = "X-Request-ID"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def request_id_from_header(value: str | None) -> str:
    """Return a bounded client request ID or a new trusted server-generated ID."""
    if value and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return uuid4().hex


def current_request_id() -> str:
    return _request_id.get()


class RecaJsonStreamHandler(logging.StreamHandler[TextIO]):
    pass


class JsonFormatter(logging.Formatter):
    """Emit stable, secret-free request log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", current_request_id()),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "environment": settings.ENVIRONMENT,
        }
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    """Configure the application logger without modifying unrelated root handlers."""
    logger = logging.getLogger("reca.api")
    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False

    if any(isinstance(handler, RecaJsonStreamHandler) for handler in logger.handlers):
        return

    handler = RecaJsonStreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach a safe request ID and log only request metadata, never request content."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request_id_from_header(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        token = _request_id.set(request_id)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            logging.getLogger("reca.api").error(
                "request.unhandled_exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "request_id": request_id,
                },
            )
            raise
        finally:
            logging.getLogger("reca.api").info(
                "request.completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                    "request_id": request_id,
                },
            )
            _request_id.reset(token)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
