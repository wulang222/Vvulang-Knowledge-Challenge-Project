"""Programmatic scoring with an optional AI narrative layer."""

import json
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime
from hashlib import sha256
from typing import Literal, cast

from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import (
    Attempt,
    GeneratedQuizDraft,
    LearningReport,
    MasteryItem,
    MasteryStatus,
    QuestionResult,
    QuizResult,
    ReportGeneratedBy,
    ReportNarrative,
    SubmissionOutcome,
)
from ai_quiz.providers.base import ReportGenerator

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def hash_attempts(attempts: list[Attempt]) -> str:
    canonical = [
        attempt.model_dump(mode="json") for attempt in sorted(attempts, key=lambda x: x.question_id)
    ]
    return sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class SubmissionService:
    def __init__(self, *, report_generator: ReportGenerator, clock: Clock = utc_now) -> None:
        self._report_generator = report_generator
        self._clock = clock

    async def evaluate(
        self,
        quiz: GeneratedQuizDraft,
        attempts: list[Attempt],
    ) -> SubmissionOutcome:
        attempt_map = self._validate_attempts(quiz, attempts)
        question_results: list[QuestionResult] = []
        for question in quiz.questions:
            attempt = attempt_map[question.id]
            question_results.append(
                QuestionResult(
                    question_id=question.id,
                    knowledge_point_id=question.knowledge_point_id,
                    selected_answers=attempt.selected_answers,
                    correct_answers=question.correct_answers,
                    is_correct=set(attempt.selected_answers) == set(question.correct_answers),
                    duration_ms=attempt.duration_ms,
                )
            )
        correct = sum(result.is_correct for result in question_results)
        total = cast(Literal[5, 10], len(question_results))
        result = QuizResult(
            total=total,
            correct=correct,
            accuracy=correct / total,
            duration_ms=sum(item.duration_ms for item in question_results),
            question_results=question_results,
        )
        mastery = self._mastery(quiz, question_results)
        try:
            narrative = await self._report_generator.generate_report(result=result, quiz=quiz)
            generated_by = ReportGeneratedBy.AI
        except Exception:
            narrative = self._fallback_narrative(result, mastery)
            generated_by = ReportGeneratedBy.DETERMINISTIC_FALLBACK
        report = LearningReport(
            **narrative.model_dump(),
            mastery=mastery,
            generated_by=generated_by,
        )
        return SubmissionOutcome(
            result=result,
            report=report,
            completed_at=self._clock(),
            submission_hash=hash_attempts(attempts),
        )

    @staticmethod
    def _validate_attempts(
        quiz: GeneratedQuizDraft,
        attempts: list[Attempt],
    ) -> dict[str, Attempt]:
        question_map = {question.id: question for question in quiz.questions}
        attempt_map = {attempt.question_id: attempt for attempt in attempts}
        valid = len(attempt_map) == len(attempts) == len(question_map) and set(attempt_map) == set(
            question_map
        )
        if valid:
            for question_id, attempt in attempt_map.items():
                option_ids = {option.id for option in question_map[question_id].options}
                if (
                    len(attempt.selected_answers) != 1
                    or attempt.selected_answers[0] not in option_ids
                ):
                    valid = False
                    break
        if not valid:
            raise AppError(
                code=ErrorCode.INVALID_ATTEMPTS,
                message="作答记录不完整，请检查后重试",
                status_code=422,
                retryable=False,
            )
        return attempt_map

    @staticmethod
    def _mastery(
        quiz: GeneratedQuizDraft,
        question_results: list[QuestionResult],
    ) -> list[MasteryItem]:
        grouped: dict[str, list[QuestionResult]] = defaultdict(list)
        for result in question_results:
            grouped[result.knowledge_point_id].append(result)
        mastery: list[MasteryItem] = []
        for knowledge_point in quiz.knowledge_points:
            results = grouped.get(knowledge_point.id, [])
            if not results:
                continue
            correct = sum(item.is_correct for item in results)
            ratio = correct / len(results)
            status = (
                MasteryStatus.STRONG
                if ratio == 1
                else MasteryStatus.DEVELOPING
                if ratio >= 0.5
                else MasteryStatus.NEEDS_REVIEW
            )
            mastery.append(
                MasteryItem(
                    knowledge_point_id=knowledge_point.id,
                    status=status,
                    correct=correct,
                    total=len(results),
                    evidence=f"本次 {len(results)} 题答对 {correct} 题",
                )
            )
        return mastery

    @staticmethod
    def _fallback_narrative(
        result: QuizResult,
        mastery: list[MasteryItem],
    ) -> ReportNarrative:
        weak_ids = [
            item.knowledge_point_id for item in mastery if item.status is not MasteryStatus.STRONG
        ]
        next_actions = [
            f"复习知识点 {knowledge_point_id}" for knowledge_point_id in weak_ids[:3]
        ] or ["继续完成一组同主题练习"]
        return ReportNarrative(
            summary=f"本次答对 {result.correct}/{result.total} 题，结果已按作答记录计算。",
            error_patterns=[] if result.correct == result.total else ["部分知识点仍需复习"],
            next_actions=next_actions,
        )
