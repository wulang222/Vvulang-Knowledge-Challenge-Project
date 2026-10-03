"""Deterministic orchestration for source-grounded quiz generation."""

from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from urllib.parse import urlsplit

from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import (
    CreateQuizRunRequest,
    DetectedInputType,
    GeneratedRun,
    GenerationMeta,
    LearningInput,
    SourceDocument,
    SourcePolicy,
    SourceType,
    TrustTier,
)
from ai_quiz.providers.base import (
    PageFetcher,
    PageFetchFailed,
    ProviderInvalidOutput,
    ProviderRateLimited,
    ProviderTimeout,
    QuizGenerator,
    SearchProvider,
)
from ai_quiz.services.input_analysis import InputAnalyzer
from ai_quiz.services.quality_gate import QuizQualityGate

Clock = Callable[[], datetime]
PROMPT_VERSION = "question_writer@1.0.0"
PRIMARY_DOMAIN_SUFFIXES = (
    ".gov",
    ".gov.cn",
    ".edu",
    ".edu.cn",
    ".ac.cn",
)
KNOWN_PRIMARY_DOMAINS = {
    "w3.org",
    "ietf.org",
    "iso.org",
    "nist.gov",
    "docs.python.org",
    "help.aliyun.com",
    "cloud.google.com",
    "learn.microsoft.com",
    "docs.aws.amazon.com",
    "platform.openai.com",
}


def utc_now() -> datetime:
    return datetime.now(UTC)


class QuizWorkflow:
    def __init__(
        self,
        *,
        input_analyzer: InputAnalyzer,
        search_provider: SearchProvider,
        page_fetcher: PageFetcher,
        quiz_generator: QuizGenerator,
        quality_gate: QuizQualityGate,
        clock: Clock = utc_now,
        max_repairs: int = 2,
        source_limit: int = 5,
    ) -> None:
        self._input_analyzer = input_analyzer
        self._search_provider = search_provider
        self._page_fetcher = page_fetcher
        self._quiz_generator = quiz_generator
        self._quality_gate = quality_gate
        self._clock = clock
        self._max_repairs = max_repairs
        self._source_limit = source_limit

    async def create(self, request: CreateQuizRunRequest) -> GeneratedRun:
        analysis = self._input_analyzer.analyze(request.learning_input)
        normalized_input = request.learning_input.model_copy(
            update={"text": analysis.normalized_text}
        )
        effective_policy = self._effective_policy(
            analysis.detected_type,
            request.config.source_policy,
        )
        sources = await self._collect_sources(
            normalized_input,
            analysis.detected_type,
            effective_policy,
        )

        repair_issues: list[str] = []
        for _ in range(self._max_repairs + 1):
            try:
                quiz = await self._quiz_generator.generate_quiz(
                    learning_input=normalized_input,
                    analysis=analysis,
                    sources=sources,
                    config=request.config,
                    repair_issues=repair_issues,
                )
            except ProviderTimeout as exc:
                raise AppError(
                    code=ErrorCode.AI_TIMEOUT,
                    message="这次生成等太久了，请重试",
                    status_code=504,
                    retryable=True,
                ) from exc
            except ProviderRateLimited as exc:
                raise AppError(
                    code=ErrorCode.RATE_LIMITED,
                    message="请求较多，请稍后重试",
                    status_code=429,
                    retryable=True,
                ) from exc
            except ProviderInvalidOutput:
                repair_issues = ["模型输出无法解析为题目结构"]
                continue

            repair_issues = self._quality_gate.validate(
                quiz,
                sources=sources,
                config=request.config,
            )
            if not repair_issues:
                return GeneratedRun(
                    quiz=quiz,
                    meta=GenerationMeta(
                        input_type=analysis.detected_type,
                        source_policy=effective_policy,
                        sources=[source.to_summary() for source in sources],
                        prompt_version=PROMPT_VERSION,
                        model_version=self._quiz_generator.model_name,
                        generated_at=self._clock(),
                    ),
                )

        raise AppError(
            code=ErrorCode.AI_OUTPUT_INVALID,
            message="题目未通过质量检查，请重试",
            status_code=502,
            retryable=True,
            details={"issues": repair_issues[:10]},
        )

    async def _collect_sources(
        self,
        learning_input: LearningInput,
        detected_type: DetectedInputType,
        effective_policy: SourcePolicy,
    ) -> list[SourceDocument]:
        sources: list[SourceDocument] = []
        if detected_type in {DetectedInputType.USER_SOURCE, DetectedInputType.HYBRID}:
            sources.append(self._user_source(learning_input.text))

        should_search = effective_policy is SourcePolicy.OFFICIAL_ALLOWED and detected_type in {
            DetectedInputType.QUESTION,
            DetectedInputType.USER_SOURCE,
            DetectedInputType.HYBRID,
        }
        if not should_search and not sources:
            raise AppError(
                code=ErrorCode.RELIABLE_SOURCE_NOT_FOUND,
                message="当前输入没有可用于出题的资料",
                status_code=422,
                retryable=False,
            )
        if not should_search:
            return sources

        try:
            candidates = await self._search_provider.search(
                learning_input.text,
                limit=self._source_limit,
            )
        except ProviderTimeout as exc:
            raise AppError(
                code=ErrorCode.AI_TIMEOUT,
                message="联网检索超时，请重试",
                status_code=504,
                retryable=True,
            ) from exc
        except ProviderRateLimited as exc:
            raise AppError(
                code=ErrorCode.RATE_LIMITED,
                message="请求较多，请稍后重试",
                status_code=429,
                retryable=True,
            ) from exc

        if not candidates and not sources:
            raise AppError(
                code=ErrorCode.RELIABLE_SOURCE_NOT_FOUND,
                message="暂时没有找到可核验的可靠来源",
                status_code=422,
                retryable=False,
            )

        fetch_failures = 0
        for candidate in candidates:
            try:
                page = await self._page_fetcher.fetch(candidate.url)
            except PageFetchFailed:
                fetch_failures += 1
                continue
            source_index = (
                len([item for item in sources if item.type is SourceType.OFFICIAL_WEB]) + 1
            )
            sources.append(
                SourceDocument(
                    source_id=f"src_web_{source_index}",
                    type=SourceType.OFFICIAL_WEB,
                    title=page.title or candidate.title or page.url,
                    publisher=page.publisher,
                    url=page.url,
                    retrieved_at=page.retrieved_at,
                    content_hash=sha256(page.content.encode()).hexdigest(),
                    trust_tier=self._trust_tier(page.url),
                    content=page.content,
                )
            )

        if not sources:
            code = (
                ErrorCode.SOURCE_FETCH_FAILED
                if fetch_failures
                else ErrorCode.RELIABLE_SOURCE_NOT_FOUND
            )
            raise AppError(
                code=code,
                message="可靠来源暂时无法读取，请重试或补充原文",
                status_code=502 if fetch_failures else 422,
                retryable=bool(fetch_failures),
            )
        return sources

    @staticmethod
    def _user_source(text: str) -> SourceDocument:
        return SourceDocument(
            source_id="src_user_1",
            type=SourceType.USER_TEXT,
            title="用户提供的学习资料",
            publisher=None,
            url=None,
            retrieved_at=None,
            content_hash=sha256(text.encode()).hexdigest(),
            trust_tier=TrustTier.USER_PROVIDED,
            content=text,
        )

    @staticmethod
    def _effective_policy(
        detected_type: DetectedInputType,
        configured: SourcePolicy,
    ) -> SourcePolicy:
        if configured is SourcePolicy.USER_ONLY:
            return SourcePolicy.USER_ONLY
        if detected_type is DetectedInputType.USER_SOURCE and configured is SourcePolicy.AUTO:
            return SourcePolicy.USER_ONLY
        return SourcePolicy.OFFICIAL_ALLOWED

    @staticmethod
    def _trust_tier(url: str) -> TrustTier:
        hostname = (urlsplit(url).hostname or "").casefold()
        if hostname in KNOWN_PRIMARY_DOMAINS or hostname.endswith(PRIMARY_DOMAIN_SUFFIXES):
            return TrustTier.OFFICIAL_PRIMARY
        return TrustTier.AUTHORITATIVE_SECONDARY
