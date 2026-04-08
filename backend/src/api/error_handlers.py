from __future__ import annotations

import traceback

import numpy as np
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.common import get_request_id
from src.core.exceptions import (
    ConfigurationError,
    FileFormatError,
    FormulaError,
    ProcessingError,
    ValidationError,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _json_safe(value):
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def register_error_handlers(app) -> None:
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc: ValidationError):
        logger.warning(f"Validation error: {exc.message}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.message,
                "code": "VALIDATION_ERROR",
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(FileFormatError)
    async def file_format_error_handler(request, exc: FileFormatError):
        logger.warning(f"File format error: {exc.message}")
        return JSONResponse(
            status_code=400,
            content={
                "detail": exc.message,
                "code": "FILE_FORMAT_ERROR",
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(ProcessingError)
    async def processing_error_handler(request, exc: ProcessingError):
        logger.error(f"Processing error: {exc.message}")
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message,
                "code": "PROCESSING_ERROR",
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(FormulaError)
    async def formula_error_handler(request, exc: FormulaError):
        logger.warning(f"Formula error: {exc.message}")
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.message,
                "code": "FORMULA_ERROR",
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(request, exc: ConfigurationError):
        logger.error(f"Configuration error: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": exc.message,
                "code": "CONFIGURATION_ERROR",
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request, exc: RequestValidationError):
        logger.warning("Request validation error")
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed.",
                "code": "REQUEST_VALIDATION_ERROR",
                "request_id": get_request_id(request),
                "errors": _json_safe(exc.errors()),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed"
        code = "HTTP_ERROR"
        errors = None

        if isinstance(detail, dict):
            message = str(detail.get("detail", message))
            maybe_code = detail.get("code")
            if isinstance(maybe_code, str) and maybe_code:
                code = maybe_code
            maybe_errors = detail.get("errors")
            if maybe_errors is not None:
                errors = _json_safe(maybe_errors)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": message,
                "code": code,
                "request_id": get_request_id(request),
                "errors": errors,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred on the server.",
                "code": "INTERNAL_SERVER_ERROR",
                "request_id": get_request_id(request),
            },
        )
