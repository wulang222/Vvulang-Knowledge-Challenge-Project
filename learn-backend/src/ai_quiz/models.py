"""Strongly typed contracts shared by the workflow and HTTP layer."""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ai_quiz.domain.quiz_run import RunStatus


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", use_enum_values=False)


class DeclaredInputType(StrEnum):
    AUTO = "AUTO"
    QUESTION = "QUESTION"
    USER_SOURCE = "USER_SOURCE"


class DetectedInputType(StrEnum):
    QUESTION = "QUESTION"
    USER_SOURCE = "USER_SOURCE"
    HYBRID = "HYBRID"


class SafetyStatus(StrEnum):
    PASS = "PASS"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class Difficulty(StrEnum):
    BASIC = "basic"
    ADVANCED = "advanced"


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    TRUE_FALSE = "true_false"


class SourcePolicy(StrEnum):
    AUTO = "AUTO"
    USER_ONLY = "USER_ONLY"
    OFFICIAL_ALLOWED = "OFFICIAL_ALLOWED"


class SourceType(StrEnum):
    USER_TEXT = "USER_TEXT"
    OFFICIAL_WEB = "OFFICIAL_WEB"


class TrustTier(StrEnum):
    USER_PROVIDED = "USER_PROVIDED"
    OFFICIAL_PRIMARY = "OFFICIAL_PRIMARY"
    AUTHORITATIVE_SECONDARY = "AUTHORITATIVE_SECONDARY"


class MasteryStatus(StrEnum):
    STRONG = "strong"
    DEVELOPING = "developing"
    NEEDS_REVIEW = "needs_review"


class ReportGeneratedBy(StrEnum):
    AI = "ai"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class LearningInput(ContractModel):
    text: str = Field(min_length=1)
    declared_type: DeclaredInputType = DeclaredInputType.AUTO


class QuizConfig(ContractModel):
    question_count: Literal[5, 10] = 5
    difficulty: Difficulty = Difficulty.BASIC
    question_types: list[QuestionType] = Field(
        default_factory=lambda: [QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE],
        min_length=1,
        max_length=2,
    )
    source_policy: SourcePolicy = SourcePolicy.AUTO
    language: Literal["zh-CN"] = "zh-CN"


class CreateQuizRunRequest(ContractModel):
    learning_input: LearningInput
    config: QuizConfig


class InputAnalysis(ContractModel):
    normalized_text: str
    detected_type: DetectedInputType
    safety_status: SafetyStatus = SafetyStatus.PASS


class SourceSummary(ContractModel):
    source_id: str
    type: SourceType
    title: str
    publisher: str | None
    url: str | None
    retrieved_at: datetime | None
    content_hash: str
    trust_tier: TrustTier


class SourceDocument(SourceSummary):
    content: str

    def to_summary(self) -> SourceSummary:
        return SourceSummary.model_validate(self.model_dump(exclude={"content"}))


class KnowledgePoint(ContractModel):
    id: str
    name: str = Field(min_length=1, max_length=60)
    importance: int = Field(ge=1, le=3)


class QuestionOption(ContractModel):
    id: str = Field(min_length=1, max_length=16)
    text: str = Field(min_length=1, max_length=300)


class SourceReference(ContractModel):
    source_id: str
    evidence_quote: str = Field(min_length=1, max_length=1500)
    location: str = Field(min_length=1, max_length=300)


class Question(ContractModel):
    id: str
    type: QuestionType
    knowledge_point_id: str
    stem: str = Field(min_length=1, max_length=500)
    options: list[QuestionOption] = Field(min_length=2, max_length=4)
    correct_answers: list[str] = Field(min_length=1, max_length=1)
    explanation: str = Field(min_length=1, max_length=1000)
    difficulty: Literal[1, 2]
    source_refs: list[SourceReference] = Field(min_length=1)


class GeneratedQuizDraft(ContractModel):
    title: str = Field(min_length=1, max_length=80)
    knowledge_points: list[KnowledgePoint] = Field(min_length=1)
    questions: list[Question] = Field(min_length=1, max_length=10)


class GenerationMeta(ContractModel):
    input_type: DetectedInputType
    source_policy: SourcePolicy
    sources: list[SourceSummary] = Field(min_length=1)
    prompt_version: str
    model_version: str
    generated_at: datetime


class GeneratedRun(ContractModel):
    quiz: GeneratedQuizDraft
    meta: GenerationMeta


class Attempt(ContractModel):
    question_id: str
    selected_answers: list[str] = Field(min_length=1, max_length=1)
    duration_ms: int = Field(ge=0, le=86400000)
    confidence: Literal["sure", "unsure", "guessed"] | None = None


class SubmitQuizRunRequest(ContractModel):
    attempts: list[Attempt] = Field(min_length=5, max_length=10)


class QuestionResult(ContractModel):
    question_id: str
    knowledge_point_id: str
    selected_answers: list[str]
    correct_answers: list[str]
    is_correct: bool
    duration_ms: int


class QuizResult(ContractModel):
    total: Literal[5, 10]
    correct: int = Field(ge=0, le=10)
    accuracy: float = Field(ge=0, le=1)
    duration_ms: int = Field(ge=0)
    question_results: list[QuestionResult] = Field(min_length=5, max_length=10)


class MasteryItem(ContractModel):
    knowledge_point_id: str
    status: MasteryStatus
    correct: int = Field(ge=0)
    total: int = Field(ge=1)
    evidence: str


class ReportNarrative(ContractModel):
    summary: str = Field(min_length=1, max_length=1000)
    error_patterns: list[str]
    next_actions: list[str] = Field(min_length=1, max_length=5)


class LearningReport(ReportNarrative):
    mastery: list[MasteryItem]
    generated_by: ReportGeneratedBy


class SubmissionOutcome(ContractModel):
    result: QuizResult
    report: LearningReport
    completed_at: datetime
    submission_hash: str


class StoredQuizRun(ContractModel):
    quiz: GeneratedQuizDraft
    meta: GenerationMeta
    result: QuizResult | None = None
    report: LearningReport | None = None
    completed_at: datetime | None = None
    submission_hash: str | None = None


class QuizRunResponse(ContractModel):
    request_id: str
    run_id: str
    status: RunStatus
    quiz: GeneratedQuizDraft
    meta: GenerationMeta
    created_at: datetime
    expires_at: datetime


class QuizRunDetailResponse(QuizRunResponse):
    result: QuizResult | None
    report: LearningReport | None


class SubmitQuizRunResponse(ContractModel):
    request_id: str
    run_id: str
    status: Literal[RunStatus.COMPLETED] = RunStatus.COMPLETED
    result: QuizResult
    report: LearningReport
    completed_at: datetime
