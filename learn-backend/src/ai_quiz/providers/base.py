"""Provider boundaries used by deterministic workflow code."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ai_quiz.models import (
    GeneratedQuizDraft,
    InputAnalysis,
    LearningInput,
    QuizConfig,
    QuizResult,
    ReportNarrative,
    SourceDocument,
)


@dataclass(frozen=True, slots=True)
class SearchCandidate:
    url: str
    title: str | None = None


@dataclass(frozen=True, slots=True)
class FetchedPage:
    url: str
    title: str
    publisher: str
    content: str
    retrieved_at: datetime


class ProviderError(RuntimeError):
    pass


class ProviderTimeout(ProviderError):
    pass


class ProviderRateLimited(ProviderError):
    pass


class ProviderInvalidOutput(ProviderError):
    pass


class PageFetchFailed(ProviderError):
    def __init__(self, url: str) -> None:
        super().__init__(f"Unable to fetch source: {url}")
        self.url = url


class SearchProvider(Protocol):
    async def search(self, query: str, *, limit: int) -> list[SearchCandidate]: ...


class PageFetcher(Protocol):
    async def fetch(self, url: str) -> FetchedPage: ...


class QuizGenerator(Protocol):
    model_name: str

    async def generate_quiz(
        self,
        *,
        learning_input: LearningInput,
        analysis: InputAnalysis,
        sources: list[SourceDocument],
        config: QuizConfig,
        repair_issues: list[str],
    ) -> GeneratedQuizDraft: ...


class ReportGenerator(Protocol):
    model_name: str

    async def generate_report(
        self,
        *,
        result: QuizResult,
        quiz: GeneratedQuizDraft,
    ) -> ReportNarrative: ...
