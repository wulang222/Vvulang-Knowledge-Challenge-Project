"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI

from ai_quiz.api.operations import router as operations_router
from ai_quiz.config import Settings, get_settings
from ai_quiz.errors import install_exception_handlers
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository
from ai_quiz.request_id import install_request_id_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.quiz_run_repository = MemoryQuizRunRepository(
            ttl=timedelta(seconds=resolved_settings.quiz_run_ttl_seconds)
        )
        yield

    application = FastAPI(
        title=resolved_settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    install_request_id_middleware(application)
    install_exception_handlers(application)
    application.include_router(operations_router, prefix=resolved_settings.api_prefix)
    return application


app = create_app()
