from copy import deepcopy

from ai_quiz.services.quality_gate import QuizQualityGate
from tests.factories import quiz_config, source_document, valid_quiz_draft


def test_valid_quiz_passes_all_quality_rules() -> None:
    issues = QuizQualityGate().validate(
        valid_quiz_draft(),
        sources=[source_document()],
        config=quiz_config(),
    )

    assert issues == []


def test_gate_reports_count_duplicate_answer_and_evidence_issues() -> None:
    draft = deepcopy(valid_quiz_draft())
    draft.questions.pop()
    draft.questions[1].stem = draft.questions[0].stem
    draft.questions[0].correct_answers = ["Z"]
    draft.questions[2].source_refs[0].evidence_quote = "材料里不存在的句子"

    issues = QuizQualityGate().validate(
        draft,
        sources=[source_document()],
        config=quiz_config(),
    )

    assert "题目数量必须为 5" in issues
    assert "题干不能重复" in issues
    assert "q_1 的正确答案必须指向已有选项" in issues
    assert "q_3 的证据片段无法在来源中定位" in issues


def test_gate_rejects_unknown_knowledge_point_and_source() -> None:
    draft = deepcopy(valid_quiz_draft())
    draft.questions[0].knowledge_point_id = "kp_unknown"
    draft.questions[0].source_refs[0].source_id = "src_unknown"

    issues = QuizQualityGate().validate(
        draft,
        sources=[source_document()],
        config=quiz_config(),
    )

    assert "q_1 引用了不存在的知识点" in issues
    assert "q_1 引用了不存在的来源 src_unknown" in issues
