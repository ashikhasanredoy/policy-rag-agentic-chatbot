"""
End-to-End Integration Tests for LangGraph Policy RAG Pipeline.
Verifies real retrieval, dynamic decomposition, multi-document synthesis,
strict refusal, citation grounding, and cross-lingual equivalence.
"""

import pytest
from src.workflow.graph import run_policy_rag


def test_e2e_english_exact_query():
    """Verify end-to-end question answering for an exact policy ID query."""
    result = run_policy_rag("What is the procedure for leave management under HR-003?")
    assert result["is_answerable"] is True
    assert "HR-003" in result["policy_ids"]
    assert len(result["citations"]) > 0
    assert len(result["answer"]) > 50


def test_e2e_bangla_query():
    """Verify end-to-end question answering for a Bengali natural language query."""
    result = run_policy_rag("একজন কর্মচারী কীভাবে ছুটির আবেদন করতে পারে?")
    assert result["is_answerable"] is True
    assert "HR-003" in result["policy_ids"]
    assert len(result["citations"]) > 0
    # Must preserve official policy ID in citation
    assert any("HR-003" in c.get("policy_id", "") for c in result["citations"])


def test_e2e_unanswerable_refusal():
    """Verify strict zero-hallucination refusal for questions not documented in policies."""
    out_of_scope_query = "What is the policy regarding bringing pet parrots, dogs, or cats into the office?"
    result = run_policy_rag(out_of_scope_query)

    assert result["is_answerable"] is False
    assert "I could not find sufficient supporting information" in result["answer"]
    assert result["confidence"] == 0.0


def test_e2e_negative_allowance_refusal():
    """Verify refusal for non-existent $1,000 entertainment allowance."""
    result = run_policy_rag("Does the company provide a $1,000 monthly entertainment allowance?")
    assert result["is_answerable"] is False
    assert "could not find sufficient supporting information" in result["answer"].lower()
    assert result["confidence"] == 0.0


def test_e2e_comparative_retrieval():
    """Verify comparative decomposition and dual-policy retrieval."""
    query = "Explain the differences between Information Security Policy and Network Security Policy."
    result = run_policy_rag(query)
    assert result["is_answerable"] is True
    pids = result["policy_ids"]
    assert "IT-001" in pids or "IT-005" in pids
    assert "IT-001" in result["answer"] and "IT-005" in result["answer"]


def test_e2e_multi_document_thematic_discovery():
    """Verify multi-document discovery for employee misconduct."""
    query = "Find all policies related to employee misconduct, investigation, and disciplinary action."
    result = run_policy_rag(query)
    assert result["is_answerable"] is True
    pids = result["policy_ids"]
    # Should retrieve multiple misconduct & disciplinary policies
    expected = {"HR-001", "HR-014", "HR-013", "LEG-004"}
    overlap = set(pids).intersection(expected)
    assert len(overlap) >= 2


def test_e2e_supplier_evaluation_and_approval():
    """Verify operational routing for supplier evaluation (PROC-002, FIN-012)."""
    query = "How does the company evaluate and approve new suppliers?"
    result = run_policy_rag(query)
    assert result["is_answerable"] is True
    pids = result["policy_ids"]
    assert "PROC-002" in pids or "PROC-006" in pids
    assert "PROC-002" in result["answer"]
    assert "FIN-012" in result["answer"]
