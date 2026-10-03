from datetime import UTC, datetime
from typing import Literal

from ai_quiz.models import (
    Difficulty,
    GeneratedQuizDraft,
    KnowledgePoint,
    Question,
    QuestionOption,
    QuestionType,
    QuizConfig,
    SourceDocument,
    SourcePolicy,
    SourceReference,
    SourceType,
    TrustTier,
)

EVIDENCE = "RAG 会先检索相关信息，再将检索结果加入上下文后生成回答。"


def quiz_config(*, count: Literal[5, 10] = 5) -> QuizConfig:
    return QuizConfig(
        question_count=count,
        difficulty=Difficulty.BASIC,
        question_types=[QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE],
        source_policy=SourcePolicy.AUTO,
    )


def source_document(
    *,
    source_id: str = "src_user_1",
    content: str = f"这是用户提供的学习资料。{EVIDENCE}",
) -> SourceDocument:
    return SourceDocument(
        source_id=source_id,
        type=SourceType.USER_TEXT,
        title="用户提供的学习资料",
        publisher=None,
        url=None,
        retrieved_at=None,
        content_hash="hash-user",
        trust_tier=TrustTier.USER_PROVIDED,
        content=content,
    )


def official_source_document() -> SourceDocument:
    return SourceDocument(
        source_id="src_web_1",
        type=SourceType.OFFICIAL_WEB,
        title="RAG 官方文档",
        publisher="Example University",
        url="https://docs.example.edu/rag",
        retrieved_at=datetime(2026, 10, 3, tzinfo=UTC),
        content_hash="hash-web",
        trust_tier=TrustTier.OFFICIAL_PRIMARY,
        content=EVIDENCE,
    )


def valid_quiz_draft(*, count: int = 5, source_id: str = "src_user_1") -> GeneratedQuizDraft:
    knowledge_point = KnowledgePoint(id="kp_1", name="RAG 基本流程", importance=3)
    questions = []
    for index in range(1, count + 1):
        questions.append(
            Question(
                id=f"q_{index}",
                type=QuestionType.SINGLE_CHOICE,
                knowledge_point_id="kp_1",
                stem=f"第 {index} 题：RAG 在生成回答前会做什么？",
                options=[
                    QuestionOption(id="A", text="检索相关信息"),
                    QuestionOption(id="B", text="删除全部资料"),
                    QuestionOption(id="C", text="跳过上下文"),
                    QuestionOption(id="D", text="只生成随机内容"),
                ],
                correct_answers=["A"],
                explanation="材料说明 RAG 会先检索，再结合上下文生成。",
                difficulty=1,
                source_refs=[
                    SourceReference(
                        source_id=source_id,
                        evidence_quote=EVIDENCE,
                        location="正文第 1 段",
                    )
                ],
            )
        )
    return GeneratedQuizDraft(
        title="RAG 基础闯关",
        knowledge_points=[knowledge_point],
        questions=questions,
    )
