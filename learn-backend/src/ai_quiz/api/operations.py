"""Free health and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict

from ai_quiz.config import Settings

router = APIRouter(tags=["Operations"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"] = "ok"


class ReadinessChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dashscope_api_key: bool
    dashscope_base_url: bool
    generation_model: bool


class ReadyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]
    checks: ReadinessChecks


@router.get("/health", response_model=HealthResponse, operation_id="getHealth")
async def get_health() -> HealthResponse:
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse, "description": "必要配置缺失"}},
    operation_id="getReadiness",
)
async def get_readiness(request: Request, response: Response) -> ReadyResponse:
    settings: Settings = request.app.state.settings
    checks = ReadinessChecks(**settings.readiness_checks())
    if not settings.is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="not_ready", checks=checks)
    return ReadyResponse(status="ready", checks=checks)
