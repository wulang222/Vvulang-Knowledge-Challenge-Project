"""Build and close real external adapters only when required configuration exists."""

from dataclasses import dataclass

import httpx2
from openai import AsyncOpenAI

from ai_quiz.config import Settings
from ai_quiz.providers.qwen import QwenGateway
from ai_quiz.providers.web_sources import WebPageFetcher
from ai_quiz.services.input_analysis import InputAnalyzer
from ai_quiz.services.quality_gate import QuizQualityGate
from ai_quiz.services.quiz_workflow import QuizWorkflow


@dataclass(slots=True)
class RuntimeServices:
    workflow: QuizWorkflow
    qwen: QwenGateway
    page_fetcher: WebPageFetcher

    async def aclose(self) -> None:
        await self.qwen.aclose()
        await self.page_fetcher.aclose()


def build_runtime_services(settings: Settings) -> RuntimeServices:
    if not settings.is_ready:
        raise ValueError("Model Studio configuration is incomplete")
    assert settings.dashscope_api_key is not None
    assert settings.dashscope_base_url is not None
    assert settings.generation_model is not None
    qwen = QwenGateway(
        client=AsyncOpenAI(
            api_key=settings.dashscope_api_key.get_secret_value(),
            base_url=str(settings.dashscope_base_url),
            timeout=httpx2.Timeout(connect=5, read=75, write=15, pool=5),
            max_retries=2,
        ),
        generation_model=settings.generation_model,
        search_model=settings.search_model or settings.generation_model,
    )
    page_fetcher = WebPageFetcher(
        client=httpx2.AsyncClient(
            timeout=httpx2.Timeout(connect=5, read=20, write=10, pool=5),
            follow_redirects=False,
            headers={"User-Agent": "AIQuizSourceFetcher/1.0"},
        )
    )
    workflow = QuizWorkflow(
        input_analyzer=InputAnalyzer(),
        search_provider=qwen,
        page_fetcher=page_fetcher,
        quiz_generator=qwen,
        quality_gate=QuizQualityGate(),
    )
    return RuntimeServices(workflow=workflow, qwen=qwen, page_fetcher=page_fetcher)
