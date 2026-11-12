"""
Unit tests for BM25 Retriever, Chroma Vector Retriever, and RRF Ensemble Retriever.
"""

import pytest
from src.retrievers.bm25_retriever import bm25_retriever
from src.retrievers.vector_retriever import chroma_retriever
from src.retrievers.ensemble_retriever import ensemble_retriever


@pytest.fixture(scope="module", autouse=True)
def ensure_indexes():
    bm25_retriever._ensure_loaded()


def test_bm25_exact_id_retrieval():
    """Verify BM25 prioritizes exact policy ID matches to rank 1."""
    results = bm25_retriever.search("What is HR-003?", top_k=5)
    assert len(results) > 0
    top_meta = results[0].get("metadata", {})
    assert top_meta.get("policy_id") == "HR-003", f"Expected HR-003, got {top_meta.get('policy_id')}"


def test_chroma_vector_search():
    """Verify Chroma vector search returns relevant candidates with metadata."""
    results = chroma_retriever.search("employee annual leave policy", top_k=5)
    assert len(results) > 0
    first = results[0]
    assert "chunk_id" in first
    assert "metadata" in first
    assert "policy_id" in first["metadata"]


def test_rrf_ensemble_fusion():
    """Verify RRF merges candidates from both retrievers with valid scores."""
    results = ensemble_retriever.retrieve("expense reimbursement approval limits", vector_top_k=10, bm25_top_k=10)
    assert len(results) > 0
    assert "rrf_score" in results[0]
    # Scores should be in descending order
    scores = [r["rrf_score"] for r in results]
    assert scores == sorted(scores, reverse=True)

