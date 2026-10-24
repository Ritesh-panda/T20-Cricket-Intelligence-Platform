"""Standardized API Error Handlers and Exceptions.

Provides consistent, safe error responses that avoid leaking internal database
exceptions, stack traces, or credentials to client callers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger("api_errors")


class ErrorResponse(BaseModel):
    """Consistent, safe error envelope for all client-facing errors."""
    error: str = Field(description="Error category or code")
    message: str = Field(description="Human-readable safe explanation")
    detail: Optional[Any] = Field(default=None, description="Detailed validation breakdown if safe")
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class APIError(Exception):
    """Base exception for application-level API errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error: str = "BadRequest",
        detail: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error = error
        self.detail = detail


class ResourceNotFoundError(APIError):
    """Raised when an entity, match, article, or resource does not exist."""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with ID '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error="ResourceNotFound",
        )


class InvalidParameterError(APIError):
    """Raised when query or path parameters violate domain constraints."""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error="InvalidParameter",
            detail=detail,
        )


class DatabaseError(APIError):
    """Raised when an internal database or persistence error occurs."""

    def __init__(self, message: str = "A database error occurred while processing the request."):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="DatabaseError",
        )


def register_error_handlers(app: FastAPI) -> None:
    """Registers exception handlers on the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        payload = ErrorResponse(
            error=exc.error,
            message=exc.message,
            detail=exc.detail,
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Simplify error details without leaking internal validation internals
        clean_errors = []
        for err in exc.errors():
            loc = " -> ".join([str(x) for x in err.get("loc", []) if x != "body"])
            msg = err.get("msg", "Invalid value")
            clean_errors.append(f"{loc}: {msg}" if loc else msg)

        payload = ErrorResponse(
            error="ValidationError",
            message="Request parameter validation failed.",
            detail=clean_errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
        payload = ErrorResponse(
            error="InternalServerError",
            message="An unexpected server error occurred. Please consult system logs.",
            detail=None,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(mode="json"),
        )
