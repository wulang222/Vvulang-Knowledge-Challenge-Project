from collections.abc import Sequence
from copy import deepcopy
from datetime import UTC, datetime

import pytest

from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import (
    CreateQuizRunRequest,
    GeneratedQuizDraft,
    InputAnalysis,
    LearningInput,
    SourceDocument,
)
from ai_quiz.providers.base import (
    FetchedPage,
    PageFetchFailed,
    ProviderTimeout,
    SearchCandidate,
)
from ai_quiz.services.input_analysis import InputAnalyzer
from ai_quiz.services.quality_gate import QuizQualityGate
from ai_quiz.services.quiz_workflow import QuizWorkflow
from tests.factories import EVIDENCE, quiz_config, valid_quiz_draft


class FakeSearchProvider:
    def __init__(self, candidates: Sequence[SearchCandidate]) -> None:
        self.candidates = list(candidates)
        self.calls: list[str] = []

    async def search(self, query: str, *, limit: int) -> list[SearchCandidate]:
        self.calls.append(query)
        return self.candidates[:limit]


class FakePageFetcher:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[str] = []

    async def fetch(self, url: str) -> FetchedPage:
        self.calls.append(url)
        if self.fail:
            raise PageFetchFailed(url)
        return FetchedPage(
            url=url,
            title="RAG 官方文档",
            publisher="Example University",
            content=EVIDENCE,
            retrieved_at=datetime(2026, 10, 3, tzinfo=UTC),
        )


class FakeQuizGenerator:
    model_name = "fake-qwen"

    def __init__(
        self,
        drafts: Sequence[GeneratedQuizDraft] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.drafts = list(drafts or [])
        self.error = error
        self.calls: list[tuple[list[SourceDocument], list[str]]] = []

    async def generate_quiz(
        self,
        *,
        learning_input: LearningInput,
        analysis: InputAnalysis,
        sources: list[SourceDocument],
        config: object,
        repair_issues: list[str],
    ) -> GeneratedQuizDraft:
        del learning_input, analysis, config
        self.calls.append((sources, repair_issues))
        if self.error:
            raise self.error
        return self.drafts.pop(0)


def make_workflow(
    *,
    search: FakeSearchProvider,
    fetcher: FakePageFetcher,
    generator: FakeQuizGenerator,
) -> QuizWorkflow:
    return QuizWorkflow(
        input_analyzer=InputAnalyzer(),
        search_provider=search,
        page_fetcher=fetcher,
        quiz_generator=generator,
        quality_gate=QuizQualityGate(),
        clock=lambda: datetime(2026, 10, 3, tzinfo=UTC),
    )


@pytest.mark.anyio
async def test_question_mode_fetches_official_sources_and_generates_quiz() -> None:
    candidate = SearchCandidate(url="https://docs.example.edu/rag", title="RAG 官方文档")
    search = FakeSearchProvider([candidate])
    fetcher = FakePageFetcher()
    generator = FakeQuizGenerator([valid_quiz_draft(source_id="src_web_1")])
    workflow = make_workflow(search=search, fetcher=fetcher, generator=generator)

    generated = await workflow.create(
        CreateQuizRunRequest(
            learning_input=LearningInput(text="RAG 是什么？"), config=quiz_config()
        )
    )

    assert search.calls == ["RAG 是什么？"]
    assert fetcher.calls == [candidate.url]
    assert generated.meta.input_type.value == "QUESTION"
    assert generated.meta.sources[0].type.value == "OFFICIAL_WEB"
    assert len(generated.quiz.questions) == 5


@pytest.mark.anyio
async def test_user_source_mode_does_not_require_web_search() -> None:
    search = FakeSearchProvider([])
    generator = FakeQuizGenerator([valid_quiz_draft()])
    workflow = make_workflow(search=search, fetcher=FakePageFetcher(), generator=generator)

    generated = await workflow.create(
        CreateQuizRunRequest(
            learning_input=LearningInput(text=f"这是概念说明。{EVIDENCE}"),
            config=quiz_config(),
        )
    )

    assert search.calls == []
    assert generated.meta.sources[0].type.value == "USER_TEXT"


@pytest.mark.anyio
async def test_workflow_repairs_invalid_quiz_with_bounded_retry() -> None:
    invalid = deepcopy(valid_quiz_draft())
    invalid.questions.pop()
    generator = FakeQuizGenerator([invalid, valid_quiz_draft()])
    workflow = make_workflow(
        search=FakeSearchProvider([]),
        fetcher=FakePageFetcher(),
        generator=generator,
    )

    generated = await workflow.create(
        CreateQuizRunRequest(
            learning_input=LearningInput(text=f"这是概念说明。{EVIDENCE}"),
            config=quiz_config(),
        )
    )

    assert len(generator.calls) == 2
    assert generator.calls[1][1] == ["题目数量必须为 5"]
    assert len(generated.quiz.questions) == 5


@pytest.mark.anyio
async def test_missing_search_results_do_not_fall_back_to_model_knowledge() -> None:
    workflow = make_workflow(
        search=FakeSearchProvider([]),
        fetcher=FakePageFetcher(),
        generator=FakeQuizGenerator([]),
    )

    with pytest.raises(AppError) as error:
        await workflow.create(
            CreateQuizRunRequest(
                learning_input=LearningInput(text="RAG 是什么？"),
                config=quiz_config(),
            )
        )

    assert error.value.code is ErrorCode.RELIABLE_SOURCE_NOT_FOUND


@pytest.mark.anyio
async def test_all_source_fetches_failing_returns_fetch_error() -> None:
    workflow = make_workflow(
        search=FakeSearchProvider(
            [SearchCandidate(url="https://docs.example.edu/rag", title="RAG")]
        ),
        fetcher=FakePageFetcher(fail=True),
        generator=FakeQuizGenerator([]),
    )

    with pytest.raises(AppError) as error:
        await workflow.create(
            CreateQuizRunRequest(
                learning_input=LearningInput(text="RAG 是什么？"),
                config=quiz_config(),
            )
        )

    assert error.value.code is ErrorCode.SOURCE_FETCH_FAILED


@pytest.mark.anyio
async def test_model_timeout_maps_to_public_timeout_error() -> None:
    workflow = make_workflow(
        search=FakeSearchProvider([]),
        fetcher=FakePageFetcher(),
        generator=FakeQuizGenerator(error=ProviderTimeout("generation timed out")),
    )

    with pytest.raises(AppError) as error:
        await workflow.create(
            CreateQuizRunRequest(
                learning_input=LearningInput(text=f"这是概念说明。{EVIDENCE}"),
                config=quiz_config(),
            )
        )

    assert error.value.code is ErrorCode.AI_TIMEOUT
