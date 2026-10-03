"""Deterministic checks that model output must pass before reaching users."""

import re

from ai_quiz.models import GeneratedQuizDraft, QuestionType, QuizConfig, SourceDocument


def normalize_evidence(text: str) -> str:
    return re.sub(r"\s+", "", text)


class QuizQualityGate:
    def validate(
        self,
        quiz: GeneratedQuizDraft,
        *,
        sources: list[SourceDocument],
        config: QuizConfig,
    ) -> list[str]:
        issues: list[str] = []
        if len(quiz.questions) != config.question_count:
            issues.append(f"题目数量必须为 {config.question_count}")

        question_ids = [question.id for question in quiz.questions]
        if len(question_ids) != len(set(question_ids)):
            issues.append("题目 ID 不能重复")
        stems = [normalize_evidence(question.stem).casefold() for question in quiz.questions]
        if len(stems) != len(set(stems)):
            issues.append("题干不能重复")

        knowledge_point_ids = {item.id for item in quiz.knowledge_points}
        source_map = {source.source_id: source for source in sources}
        for question in quiz.questions:
            if question.knowledge_point_id not in knowledge_point_ids:
                issues.append(f"{question.id} 引用了不存在的知识点")
            if question.type not in config.question_types:
                issues.append(f"{question.id} 使用了未请求的题型")
            expected_options = 4 if question.type is QuestionType.SINGLE_CHOICE else 2
            if len(question.options) != expected_options:
                issues.append(f"{question.id} 必须包含 {expected_options} 个选项")
            option_ids = [option.id for option in question.options]
            if len(option_ids) != len(set(option_ids)):
                issues.append(f"{question.id} 的选项 ID 不能重复")
            if len(question.correct_answers) != 1 or question.correct_answers[0] not in option_ids:
                issues.append(f"{question.id} 的正确答案必须指向已有选项")
            for reference in question.source_refs:
                source = source_map.get(reference.source_id)
                if source is None:
                    issues.append(f"{question.id} 引用了不存在的来源 {reference.source_id}")
                    continue
                if normalize_evidence(reference.evidence_quote) not in normalize_evidence(
                    source.content
                ):
                    issues.append(f"{question.id} 的证据片段无法在来源中定位")
        return issues
