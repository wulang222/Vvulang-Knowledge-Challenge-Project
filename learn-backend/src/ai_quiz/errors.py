"""Sanitized public error envelope shared by all API endpoints."""

import logging
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai_quiz.request_id import request_id_from

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


def _error_response(request: Request, error: AppError) -> JSONResponse:
    request_id = request_id_from(request)
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

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        if request.url.path.endswith("/submit"):
            error = AppError(
                code=ErrorCode.INVALID_ATTEMPTS,
                message="作答记录不完整，请检查后重试",
                status_code=422,
                retryable=False,
            )
        else:
            body = exc.body
            text = None
            if isinstance(body, dict):
                learning_input = body.get("learning_input")
                if isinstance(learning_input, dict):
                    candidate = learning_input.get("text")
                    text = candidate if isinstance(candidate, str) else None
            is_empty = text is not None and not text.strip()
            error = AppError(
                code=ErrorCode.EMPTY_INPUT if is_empty else ErrorCode.CONTENT_NOT_ALLOWED,
                message=("输入一个问题、主题或资料" if is_empty else "请求参数不符合闯关配置要求"),
                status_code=422,
                retryable=False,
            )
        return _error_response(request, error)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = request_id_from(request)
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
