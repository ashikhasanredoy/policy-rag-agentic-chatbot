import pytest
from backend.app.rag.rrf import reciprocal_rank_fusion
from backend.app.graders.answerability import answerability_grader
from backend.app.graders.relevance import relevance_grader
from backend.app.graders.faithfulness import faithfulness_grader

def test_rrf_fusion():
    list_a = [
        {"text": "Doc A", "metadata": {"chunk_id": "a"}},
        {"text": "Doc B", "metadata": {"chunk_id": "b"}},
        {"text": "Doc C", "metadata": {"chunk_id": "c"}},
    ]
    list_b = [
        {"text": "Doc B", "metadata": {"chunk_id": "b"}},
        {"text": "Doc A", "metadata": {"chunk_id": "a"}},
        {"text": "Doc D", "metadata": {"chunk_id": "d"}},
    ]

    fused = reciprocal_rank_fusion([list_a, list_b], k=60, top_n=4)
    assert len(fused) == 4
    top_ids = [d["metadata"]["chunk_id"] for d in fused[:2]]
    # Doc A and Doc B should rank highest because they appear in both lists
    assert "a" in top_ids and "b" in top_ids

def test_answerability_abstention_guardrail():
    # Context that mentions travel, but user asks about housing allowance
    context = [{"text": "Travel reimbursement covers up to $75 daily meal allowance.", "rerank_score": 0.3}]
    is_answerable, confidence, reason = answerability_grader.grade("Does company give housing allowance?", context)
    assert is_answerable is False
    assert confidence < 0.65

def test_answerability_success():
    context = [{"text": "Full-time employees receive 20 days paid annual leave each year.", "rerank_score": 0.95}]
    is_answerable, confidence, reason = answerability_grader.grade("How many annual leave days do full-time employees get?", context)
    assert is_answerable is True
    assert confidence >= 0.65
