from datetime import UTC, datetime

import pytest

from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import Attempt, ReportNarrative
from ai_quiz.services.submission import SubmissionService
from tests.factories import valid_quiz_draft


class FakeReportGenerator:
    model_name = "fake-report-model"

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    async def generate_report(self, *, result: object, quiz: object) -> ReportNarrative:
        del result, quiz
        if self.fail:
            raise RuntimeError("report provider failed")
        return ReportNarrative(
            summary="核心流程已掌握，继续复习来源边界。",
            error_patterns=["容易忽略检索步骤"],
            next_actions=["回看 RAG 基本流程"],
        )


def attempts(*, correct_count: int = 3) -> list[Attempt]:
    return [
        Attempt(
            question_id=f"q_{index}",
            selected_answers=["A" if index <= correct_count else "B"],
            duration_ms=index * 1000,
        )
        for index in range(1, 6)
    ]


@pytest.mark.anyio
async def test_submission_computes_objective_result_and_merges_narrative() -> None:
    service = SubmissionService(
        report_generator=FakeReportGenerator(),
        clock=lambda: datetime(2026, 10, 3, tzinfo=UTC),
    )

    outcome = await service.evaluate(valid_quiz_draft(), attempts(correct_count=3))

    assert outcome.result.total == 5
    assert outcome.result.correct == 3
    assert outcome.result.accuracy == 0.6
    assert outcome.result.duration_ms == 15000
    assert [item.is_correct for item in outcome.result.question_results] == [
        True,
        True,
        True,
        False,
        False,
    ]
    assert outcome.report.mastery[0].status.value == "developing"
    assert outcome.report.generated_by.value == "ai"


@pytest.mark.anyio
async def test_report_failure_returns_deterministic_fallback() -> None:
    service = SubmissionService(
        report_generator=FakeReportGenerator(fail=True),
        clock=lambda: datetime(2026, 10, 3, tzinfo=UTC),
    )

    outcome = await service.evaluate(valid_quiz_draft(), attempts(correct_count=0))

    assert outcome.result.correct == 0
    assert outcome.report.generated_by.value == "deterministic_fallback"
    assert "0/5" in outcome.report.summary
    assert outcome.report.next_actions


@pytest.mark.anyio
async def test_submission_rejects_missing_duplicate_and_unknown_answers() -> None:
    service = SubmissionService(
        report_generator=FakeReportGenerator(),
        clock=lambda: datetime(2026, 10, 3, tzinfo=UTC),
    )
    invalid_attempts = attempts()
    invalid_attempts[-1] = Attempt(
        question_id="q_4",
        selected_answers=["Z"],
        duration_ms=1,
    )

    with pytest.raises(AppError) as error:
        await service.evaluate(valid_quiz_draft(), invalid_attempts)

    assert error.value.code is ErrorCode.INVALID_ATTEMPTS
