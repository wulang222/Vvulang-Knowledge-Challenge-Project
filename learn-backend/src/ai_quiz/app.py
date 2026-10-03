"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI

from ai_quiz.api.operations import router as operations_router
from ai_quiz.api.quiz_runs import QuizWorkflowRunner
from ai_quiz.api.quiz_runs import router as quiz_runs_router
from ai_quiz.config import Settings, get_settings
from ai_quiz.errors import install_exception_handlers
from ai_quiz.models import GeneratedQuizDraft, QuizResult, ReportNarrative
from ai_quiz.providers.base import ReportGenerator
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository
from ai_quiz.request_id import install_request_id_middleware
from ai_quiz.runtime import RuntimeServices, build_runtime_services
from ai_quiz.services.submission import SubmissionService


class FallbackOnlyReportGenerator:
    model_name = "deterministic-fallback"

    async def generate_report(
        self,
        *,
        result: QuizResult,
        quiz: GeneratedQuizDraft,
    ) -> ReportNarrative:
        del result, quiz
        raise RuntimeError("AI report generator is not configured")


def create_app(
    settings: Settings | None = None,
    *,
    quiz_workflow: QuizWorkflowRunner | None = None,
    report_generator: ReportGenerator | None = None,
    quiz_run_repository: MemoryQuizRunRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        runtime: RuntimeServices | None = None
        repository = quiz_run_repository or MemoryQuizRunRepository(
            ttl=timedelta(seconds=resolved_settings.quiz_run_ttl_seconds),
        )
        active_workflow = quiz_workflow
        active_report_generator = report_generator
        if resolved_settings.is_ready and (
            active_workflow is None or active_report_generator is None
        ):
            runtime = build_runtime_services(resolved_settings)
            active_workflow = active_workflow or runtime.workflow
            active_report_generator = active_report_generator or runtime.qwen
        active_report_generator = active_report_generator or FallbackOnlyReportGenerator()

        application.state.quiz_run_repository = repository
        application.state.quiz_workflow = active_workflow
        application.state.submission_service = SubmissionService(
            report_generator=active_report_generator
        )
        try:
            yield
        finally:
            if runtime is not None:
                await runtime.aclose()

    application = FastAPI(
        title=resolved_settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    install_request_id_middleware(application)
    install_exception_handlers(application)
    application.include_router(operations_router, prefix=resolved_settings.api_prefix)
    application.include_router(quiz_runs_router, prefix=resolved_settings.api_prefix)
    return application


app = create_app()
