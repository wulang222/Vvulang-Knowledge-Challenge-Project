from pydantic import AnyHttpUrl, SecretStr
from pytest import MonkeyPatch

from ai_quiz.config import Settings

TEST_BASE_URL = AnyHttpUrl("https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")


def test_settings_are_not_ready_without_paid_service_configuration() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        dashscope_api_key=None,
        dashscope_base_url=None,
        generation_model=None,
    )

    assert settings.is_ready is False
    assert settings.readiness_checks() == {
        "dashscope_api_key": False,
        "dashscope_base_url": False,
        "generation_model": False,
    }
    assert settings.quiz_run_ttl_seconds == 3600


def test_settings_are_ready_when_all_required_values_exist() -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        dashscope_api_key=SecretStr("secret-key"),
        dashscope_base_url=TEST_BASE_URL,
        generation_model="qwen-plus",
    )

    assert settings.is_ready is True
    assert all(settings.readiness_checks().values())
    assert "secret-key" not in repr(settings)


def test_settings_accept_official_dashscope_environment_names(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "from-env")
    monkeypatch.setenv(
        "DASHSCOPE_BASE_URL",
        "https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    monkeypatch.setenv("DASHSCOPE_GENERATION_MODEL", "qwen-plus")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.is_ready is True
    assert settings.dashscope_api_key == SecretStr("from-env")
