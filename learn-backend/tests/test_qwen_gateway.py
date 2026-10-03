from types import SimpleNamespace
from typing import Any, cast

import httpx2
import openai
import pytest
from openai import AsyncOpenAI
from openai.types.responses import Response

from ai_quiz.models import (
    DetectedInputType,
    InputAnalysis,
    LearningInput,
    ReportNarrative,
    SafetyStatus,
)
from ai_quiz.providers.base import ProviderInvalidOutput, ProviderTimeout
from ai_quiz.providers.qwen import QwenGateway, build_source_context, extract_search_candidates
from tests.factories import quiz_config, source_document, valid_quiz_draft


def search_response(*urls: str) -> Response:
    return Response.model_validate(
        {
            "id": "resp_search",
            "created_at": 0,
            "model": "qwen-search",
            "object": "response",
            "output": [
                {
                    "id": "search_1",
                    "type": "web_search_call",
                    "status": "completed",
                    "action": {
                        "type": "search",
                        "query": "RAG 官方文档",
                        "sources": [{"type": "url", "url": url} for url in urls],
                    },
                }
            ],
            "parallel_tool_calls": True,
            "tool_choice": "auto",
            "tools": [],
        }
    )


class FakeResponses:
    def __init__(self) -> None:
        self.create_result: object = search_response("https://docs.example.edu/rag")
        self.parse_results: list[object] = []
        self.error: Exception | None = None
        self.create_calls: list[dict[str, Any]] = []
        self.parse_calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> object:
        self.create_calls.append(kwargs)
        if self.error:
            raise self.error
        return self.create_result

    async def parse(self, **kwargs: Any) -> object:
        self.parse_calls.append(kwargs)
        if self.error:
            raise self.error
        return self.parse_results.pop(0)


class FakeOpenAI:
    def __init__(self) -> None:
        self.responses = FakeResponses()
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def gateway(fake: FakeOpenAI) -> QwenGateway:
    return QwenGateway(
        client=cast(AsyncOpenAI, fake),
        generation_model="qwen-generation",
        search_model="qwen-search",
    )


def test_extract_search_candidates_deduplicates_and_limits_sources() -> None:
    payload = search_response(
        "https://a.example/doc",
        "https://a.example/doc",
        "https://b.example/doc",
    ).model_dump(mode="json")

    candidates = extract_search_candidates(payload, limit=1)

    assert [candidate.url for candidate in candidates] == ["https://a.example/doc"]


def test_source_context_samples_long_documents_without_rejecting_them() -> None:
    source = source_document(content="开头" + "内容" * 20_000 + "结尾")

    context = build_source_context([source], max_chars=2_000)

    assert "SOURCE src_user_1" in context
    assert "开头" in context
    assert "结尾" in context
    assert len(context) < 2_500


@pytest.mark.anyio
async def test_gateway_search_uses_responses_web_tools() -> None:
    fake = FakeOpenAI()

    candidates = await gateway(fake).search("RAG 是什么？", limit=5)

    assert candidates[0].url == "https://docs.example.edu/rag"
    assert fake.responses.create_calls[0]["tools"] == [
        {"type": "web_search"},
        {"type": "web_extractor"},
    ]


@pytest.mark.anyio
async def test_gateway_parses_quiz_and_report_models() -> None:
    fake = FakeOpenAI()
    fake.responses.parse_results = [
        SimpleNamespace(output_parsed=valid_quiz_draft()),
        SimpleNamespace(
            output_parsed=ReportNarrative(
                summary="表现稳定。",
                error_patterns=[],
                next_actions=["继续练习"],
            )
        ),
    ]
    qwen = gateway(fake)

    quiz = await qwen.generate_quiz(
        learning_input=LearningInput(text="RAG 是什么？"),
        analysis=InputAnalysis(
            normalized_text="RAG 是什么？",
            detected_type=DetectedInputType.QUESTION,
            safety_status=SafetyStatus.PASS,
        ),
        sources=[source_document()],
        config=quiz_config(),
        repair_issues=[],
    )
    report = await qwen.generate_report(
        result=SimpleNamespace(model_dump=lambda **kwargs: {}, correct=5),  # type: ignore[arg-type]
        quiz=quiz,
    )
    await qwen.aclose()

    assert quiz.title == "RAG 基础闯关"
    assert report.next_actions == ["继续练习"]
    assert fake.closed is True


@pytest.mark.anyio
async def test_gateway_maps_timeout_and_missing_parsed_output() -> None:
    fake = FakeOpenAI()
    fake.responses.error = openai.APITimeoutError(
        request=httpx2.Request("POST", "https://example.com/responses")
    )

    with pytest.raises(ProviderTimeout):
        await gateway(fake).search("RAG", limit=5)

    fake.responses.error = None
    fake.responses.parse_results = [SimpleNamespace(output_parsed=None)]
    with pytest.raises(ProviderInvalidOutput):
        await gateway(fake).generate_quiz(
            learning_input=LearningInput(text="RAG"),
            analysis=InputAnalysis(
                normalized_text="RAG",
                detected_type=DetectedInputType.QUESTION,
            ),
            sources=[source_document()],
            config=quiz_config(),
            repair_issues=[],
        )
