"""Deterministic first-pass input classification and safety checks."""

import re
from collections import Counter

from ai_quiz.errors import AppError, ErrorCode
from ai_quiz.models import (
    DeclaredInputType,
    DetectedInputType,
    InputAnalysis,
    LearningInput,
)

SENSITIVE_PATTERNS = (
    re.compile(r"\b\d{17}[\dXx]\b"),
    re.compile(r"(?i)\b(?:sk|ak)-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token)\s*[:=]\s*\S{8,}"),
    re.compile(r"(?:密码|口令)\s*[:：=]\s*\S{4,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
INJECTION_PATTERNS = (
    re.compile(r"忽略(?:之前|以上|所有).{0,12}(?:指令|提示词)"),
    re.compile(r"(?:输出|泄露|显示).{0,8}(?:系统提示词|system prompt)", re.IGNORECASE),
)
QUESTION_MARKERS = (
    "?",
    "？",
    "是什么",
    "为什么",
    "如何",
    "怎么",
    "哪些",
    "是否",
    "能否",
    "请解释",
    "请说明",
)


class InputAnalyzer:
    def analyze(self, learning_input: LearningInput) -> InputAnalysis:
        text = learning_input.text.strip()
        if not text:
            raise AppError(
                code=ErrorCode.EMPTY_INPUT,
                message="输入一个问题、主题或资料",
                status_code=422,
                retryable=False,
            )
        if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
            raise AppError(
                code=ErrorCode.SENSITIVE_INFORMATION,
                message="检测到可能的敏感信息，请删除后重试",
                status_code=422,
                retryable=False,
            )
        if any(pattern.search(text) for pattern in INJECTION_PATTERNS) or self._is_garbage(text):
            raise AppError(
                code=ErrorCode.CONTENT_NOT_ALLOWED,
                message="输入内容无法用于生成学习题目，请修改后重试",
                status_code=422,
                retryable=False,
            )
        return InputAnalysis(
            normalized_text=text,
            detected_type=self._detect_type(text, learning_input.declared_type),
        )

    @staticmethod
    def _detect_type(text: str, declared_type: DeclaredInputType) -> DetectedInputType:
        if declared_type is DeclaredInputType.QUESTION:
            return DetectedInputType.QUESTION
        if declared_type is DeclaredInputType.USER_SOURCE:
            return DetectedInputType.USER_SOURCE

        has_question = any(marker in text for marker in QUESTION_MARKERS)
        sentence_count = len([part for part in re.split(r"[。！？!?\n]+", text) if part.strip()])
        looks_like_source = sentence_count >= 2 or len(text) >= 60
        if has_question and looks_like_source:
            return DetectedInputType.HYBRID
        if has_question or not looks_like_source:
            return DetectedInputType.QUESTION
        return DetectedInputType.USER_SOURCE

    @staticmethod
    def _is_garbage(text: str) -> bool:
        compact = "".join(text.split())
        if len(compact) < 24:
            return False
        _, count = Counter(compact).most_common(1)[0]
        return count / len(compact) >= 0.85
