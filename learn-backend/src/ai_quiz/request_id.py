"""Request correlation without trusting arbitrary client header content."""

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

RequestHandler = Callable[[Request], Awaitable[Response]]
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def new_request_id() -> str:
    return f"req_{uuid4().hex}"


def normalize_request_id(value: str | None) -> str:
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return new_request_id()


def install_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next: RequestHandler) -> Response:
        request_id = normalize_request_id(request.headers.get("X-Request-Id"))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
