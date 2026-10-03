from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl, SecretStr

from ai_quiz.app import create_app
from ai_quiz.config import Settings
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository

TEST_BASE_URL = AnyHttpUrl("https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")


def build_settings(*, ready: bool) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        dashscope_api_key=SecretStr("test-key") if ready else None,
        dashscope_base_url=TEST_BASE_URL if ready else None,
        generation_model="qwen-plus" if ready else None,
    )


def test_health_is_independent_from_paid_service_readiness() -> None:
    app = create_app(build_settings(ready=False))

    with TestClient(app) as client:
        response = client.get("/api/v1/health", headers={"X-Request-Id": "req-client"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-Id"] == "req-client"


def test_ready_returns_503_and_boolean_checks_when_configuration_is_missing() -> None:
    app = create_app(build_settings(ready=False))

    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "dashscope_api_key": False,
            "dashscope_base_url": False,
            "generation_model": False,
        },
    }


def test_ready_returns_200_without_calling_an_external_service() -> None:
    app = create_app(build_settings(ready=True))

    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert all(response.json()["checks"].values())


def test_lifespan_initializes_the_in_memory_repository() -> None:
    app = create_app(build_settings(ready=False))

    with TestClient(app):
        assert isinstance(app.state.quiz_run_repository, MemoryQuizRunRepository)
        assert app.state.settings.quiz_run_ttl_seconds == 3600
