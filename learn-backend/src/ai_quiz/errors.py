"""Sanitized public error envelope shared by all API endpoints."""

import logging
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ai_quiz.request_id import new_request_id

logger = logging.getLogger(__name__)


class ErrorCode(StrEnum):
    EMPTY_INPUT = "EMPTY_INPUT"
    SENSITIVE_INFORMATION = "SENSITIVE_INFORMATION"
    CONTENT_NOT_ALLOWED = "CONTENT_NOT_ALLOWED"
    RELIABLE_SOURCE_NOT_FOUND = "RELIABLE_SOURCE_NOT_FOUND"
    SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_OUTPUT_INVALID = "AI_OUTPUT_INVALID"
    INVALID_ATTEMPTS = "INVALID_ATTEMPTS"
    RUN_NOT_FOUND = "RUN_NOT_FOUND"
    RUN_EXPIRED = "RUN_EXPIRED"
    RUN_ALREADY_COMPLETED = "RUN_ALREADY_COMPLETED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        status_code: int,
        retryable: bool,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else new_request_id()


def _error_response(request: Request, error: AppError) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=error.status_code,
        headers={"X-Request-Id": request_id},
        content={
            "request_id": request_id,
            "error": {
                "code": error.code,
                "message": error.message,
                "retryable": error.retryable,
                "details": error.details,
            },
        },
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(request, exc)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id(request)
        logger.exception("Unhandled API error request_id=%s", request_id, exc_info=exc)
        return _error_response(
            request,
            AppError(
                code=ErrorCode.INTERNAL_ERROR,
                message="服务暂时不可用，请携带请求编号反馈",
                status_code=500,
                retryable=True,
            ),
        )
