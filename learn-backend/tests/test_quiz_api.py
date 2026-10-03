from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pydantic import AnyHttpUrl, SecretStr

from ai_quiz.app import create_app
from ai_quiz.config import Settings
from ai_quiz.models import (
    DetectedInputType,
    GeneratedRun,
    GenerationMeta,
    ReportNarrative,
    SourcePolicy,
)
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository
from tests.factories import source_document, valid_quiz_draft


@dataclass
class MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


class FakeWorkflow:
    async def create(self, request: object) -> GeneratedRun:
        del request
        source = source_document()
        return GeneratedRun(
            quiz=valid_quiz_draft(),
            meta=GenerationMeta(
                input_type=DetectedInputType.USER_SOURCE,
                source_policy=SourcePolicy.USER_ONLY,
                sources=[source.to_summary()],
                prompt_version="question_writer@1.0.0",
                model_version="fake-qwen",
                generated_at=datetime(2026, 10, 3, tzinfo=UTC),
            ),
        )


class FakeReportGenerator:
    model_name = "fake-report-model"

    async def generate_report(self, *, result: object, quiz: object) -> ReportNarrative:
        del result, quiz
        return ReportNarrative(
            summary="本次表现稳定。",
            error_patterns=[],
            next_actions=["再完成一组练习"],
        )


def ready_settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        dashscope_api_key=SecretStr("test-key"),
        dashscope_base_url=AnyHttpUrl(
            "https://workspace.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
        ),
        generation_model="qwen-plus",
    )


def create_payload() -> dict[str, object]:
    return {
        "learning_input": {
            "text": "这是用户原文。RAG 会先检索相关信息，再将检索结果加入上下文后生成回答。"
        },
        "config": {
            "question_count": 5,
            "difficulty": "basic",
            "question_types": ["single_choice", "true_false"],
            "source_policy": "AUTO",
        },
    }


def submit_payload(*, first_answer: str = "A") -> dict[str, object]:
    return {
        "attempts": [
            {
                "question_id": f"q_{index}",
                "selected_answers": [first_answer if index == 1 else "A"],
                "duration_ms": 1000,
            }
            for index in range(1, 6)
        ]
    }


def test_create_get_submit_and_idempotent_repeat_follow_contract() -> None:
    app = create_app(
        ready_settings(),
        quiz_workflow=FakeWorkflow(),
        report_generator=FakeReportGenerator(),
    )

    with TestClient(app) as client:
        created = client.post("/api/v1/quiz-runs", json=create_payload())
        run_id = created.json()["run_id"]
        loaded = client.get(f"/api/v1/quiz-runs/{run_id}")
        submitted = client.post(
            f"/api/v1/quiz-runs/{run_id}/submit",
            json=submit_payload(),
        )
        repeated = client.post(
            f"/api/v1/quiz-runs/{run_id}/submit",
            json=submit_payload(),
        )
        changed = client.post(
            f"/api/v1/quiz-runs/{run_id}/submit",
            json=submit_payload(first_answer="B"),
        )

    assert created.status_code == 201
    assert created.json()["status"] == "READY"
    assert len(created.json()["quiz"]["questions"]) == 5
    assert loaded.status_code == 200
    assert loaded.json()["result"] is None
    assert submitted.status_code == 200
    assert submitted.json()["result"]["correct"] == 5
    assert repeated.status_code == 200
    assert repeated.json()["result"] == submitted.json()["result"]
    assert repeated.json()["report"] == submitted.json()["report"]
    assert repeated.json()["request_id"] != submitted.json()["request_id"]
    assert changed.status_code == 409
    assert changed.json()["error"]["code"] == "RUN_ALREADY_COMPLETED"


def test_missing_and_expired_runs_return_frozen_errors() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    app = create_app(
        ready_settings(),
        quiz_workflow=FakeWorkflow(),
        report_generator=FakeReportGenerator(),
        quiz_run_repository=repository,
    )

    with TestClient(app) as client:
        missing = client.get("/api/v1/quiz-runs/run_missing")
        created = client.post("/api/v1/quiz-runs", json=create_payload())
        clock.current += timedelta(minutes=61)
        expired = client.get(f"/api/v1/quiz-runs/{created.json()['run_id']}")

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RUN_NOT_FOUND"
    assert expired.status_code == 410
    assert expired.json()["error"]["code"] == "RUN_EXPIRED"


def test_request_validation_uses_sanitized_frozen_errors() -> None:
    app = create_app(
        ready_settings(),
        quiz_workflow=FakeWorkflow(),
        report_generator=FakeReportGenerator(),
    )

    with TestClient(app) as client:
        empty = client.post(
            "/api/v1/quiz-runs",
            json={**create_payload(), "learning_input": {"text": ""}},
        )
        invalid_config = client.post(
            "/api/v1/quiz-runs",
            json={
                "learning_input": {"text": "RAG 是什么？"},
                "config": {
                    "question_count": 15,
                    "difficulty": "BASIC",
                    "question_types": ["SINGLE_CHOICE", "TRUE_FALSE"],
                    "source_preference": "AUTO",
                },
            },
        )
        invalid_attempts = client.post(
            "/api/v1/quiz-runs/run_missing/submit",
            json={"attempts": []},
        )

    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "EMPTY_INPUT"
    assert invalid_config.json()["error"]["code"] == "CONTENT_NOT_ALLOWED"
    assert invalid_attempts.json()["error"]["code"] == "INVALID_ATTEMPTS"
