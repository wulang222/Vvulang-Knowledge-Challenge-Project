from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_quiz.errors import AppError, ErrorCode, install_exception_handlers
from ai_quiz.request_id import install_request_id_middleware


def build_error_app() -> FastAPI:
    app = FastAPI()
    install_request_id_middleware(app)
    install_exception_handlers(app)

    @app.get("/expected")
    async def expected_error() -> None:
        raise AppError(
            code=ErrorCode.AI_TIMEOUT,
            message="这次生成等太久了，请重试",
            status_code=504,
            retryable=True,
        )

    @app.get("/unexpected")
    async def unexpected_error() -> None:
        raise RuntimeError("must not leak")

    return app


def test_expected_error_uses_the_frozen_error_envelope() -> None:
    with TestClient(build_error_app()) as client:
        response = client.get("/expected", headers={"X-Request-Id": "req-fixed"})

    assert response.status_code == 504
    assert response.headers["X-Request-Id"] == "req-fixed"
    assert response.json() == {
        "request_id": "req-fixed",
        "error": {
            "code": "AI_TIMEOUT",
            "message": "这次生成等太久了，请重试",
            "retryable": True,
            "details": None,
        },
    }


def test_unexpected_error_is_sanitized() -> None:
    with TestClient(build_error_app(), raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    body = response.json()
    assert response.status_code == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["retryable"] is True
    assert "must not leak" not in response.text
    assert body["request_id"].startswith("req_")


def test_invalid_or_oversized_request_id_is_replaced() -> None:
    with TestClient(build_error_app()) as client:
        response = client.get("/expected", headers={"X-Request-Id": "x" * 129})

    assert response.status_code == 504
    assert response.headers["X-Request-Id"].startswith("req_")
    assert response.json()["request_id"] == response.headers["X-Request-Id"]
