"""Anonymous quiz-run HTTP endpoints."""

from typing import Protocol, cast
from uuid import uuid4

from fastapi import APIRouter, Request, status

from ai_quiz.domain.quiz_run import (
    QuizRunExpired,
    QuizRunNotFound,
    QuizRunSnapshot,
    RunStatus,
)
from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import (
    CreateQuizRunRequest,
    GeneratedRun,
    QuizRunDetailResponse,
    QuizRunResponse,
    StoredQuizRun,
    SubmitQuizRunRequest,
    SubmitQuizRunResponse,
)
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository
from ai_quiz.request_id import request_id_from
from ai_quiz.services.submission import SubmissionService, hash_attempts

router = APIRouter(prefix="/quiz-runs", tags=["QuizRuns"])


class QuizWorkflowRunner(Protocol):
    async def create(self, request: CreateQuizRunRequest) -> GeneratedRun: ...


def _repository(request: Request) -> MemoryQuizRunRepository:
    return cast(MemoryQuizRunRepository, request.app.state.quiz_run_repository)


def _workflow(request: Request) -> QuizWorkflowRunner:
    workflow: QuizWorkflowRunner | None = request.app.state.quiz_workflow
    if workflow is None:
        raise AppError(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务尚未完成模型配置",
            status_code=500,
            retryable=True,
        )
    return workflow


def _load_snapshot(request: Request, run_id: str) -> tuple[QuizRunSnapshot, StoredQuizRun]:
    try:
        snapshot = _repository(request).get(run_id)
    except QuizRunExpired as exc:
        raise AppError(
            code=ErrorCode.RUN_EXPIRED,
            message="临时会话已过期，请用原设置重新生成",
            status_code=410,
            retryable=False,
        ) from exc
    except QuizRunNotFound as exc:
        raise AppError(
            code=ErrorCode.RUN_NOT_FOUND,
            message="没有找到本次闯关，请重新生成",
            status_code=404,
            retryable=False,
        ) from exc
    return snapshot, StoredQuizRun.model_validate(snapshot.payload)


@router.post(
    "",
    response_model=QuizRunResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createQuizRun",
)
async def create_quiz_run(
    payload: CreateQuizRunRequest,
    request: Request,
) -> QuizRunResponse:
    generated = await _workflow(request).create(payload)
    run_id = f"run_{uuid4().hex}"
    stored = StoredQuizRun(quiz=generated.quiz, meta=generated.meta)
    snapshot = _repository(request).create(run_id, stored.model_dump(mode="json"))
    return QuizRunResponse(
        request_id=request_id_from(request),
        run_id=run_id,
        status=RunStatus.READY,
        quiz=stored.quiz,
        meta=stored.meta,
        created_at=snapshot.created_at,
        expires_at=snapshot.expires_at,
    )


@router.get(
    "/{run_id}",
    response_model=QuizRunDetailResponse,
    operation_id="getQuizRun",
)
async def get_quiz_run(run_id: str, request: Request) -> QuizRunDetailResponse:
    snapshot, stored = _load_snapshot(request, run_id)
    return QuizRunDetailResponse(
        request_id=request_id_from(request),
        run_id=run_id,
        status=snapshot.status,
        quiz=stored.quiz,
        meta=stored.meta,
        created_at=snapshot.created_at,
        expires_at=snapshot.expires_at,
        result=stored.result,
        report=stored.report,
    )


@router.post(
    "/{run_id}/submit",
    response_model=SubmitQuizRunResponse,
    operation_id="submitQuizRun",
)
async def submit_quiz_run(
    run_id: str,
    payload: SubmitQuizRunRequest,
    request: Request,
) -> SubmitQuizRunResponse:
    snapshot, stored = _load_snapshot(request, run_id)
    submission_hash = hash_attempts(payload.attempts)
    if snapshot.status is RunStatus.COMPLETED:
        if (
            stored.submission_hash == submission_hash
            and stored.result is not None
            and stored.report is not None
            and stored.completed_at is not None
        ):
            return SubmitQuizRunResponse(
                request_id=request_id_from(request),
                run_id=run_id,
                result=stored.result,
                report=stored.report,
                completed_at=stored.completed_at,
            )
        raise AppError(
            code=ErrorCode.RUN_ALREADY_COMPLETED,
            message="本次闯关已完成，不能修改作答",
            status_code=409,
            retryable=False,
        )

    service: SubmissionService = request.app.state.submission_service
    outcome = await service.evaluate(stored.quiz, payload.attempts)
    completed = stored.model_copy(
        update={
            "result": outcome.result,
            "report": outcome.report,
            "completed_at": outcome.completed_at,
            "submission_hash": outcome.submission_hash,
        }
    )
    _repository(request).replace(
        run_id,
        payload=completed.model_dump(mode="json"),
        status=RunStatus.COMPLETED,
    )
    return SubmitQuizRunResponse(
        request_id=request_id_from(request),
        run_id=run_id,
        result=outcome.result,
        report=outcome.report,
        completed_at=outcome.completed_at,
    )
