"""
Unit tests for Cross-Encoder Reranker and Parent Document Enrichment.
"""

import pytest
from src.retrievers.reranker import cross_encoder_reranker
from src.retrievers.parent_retriever import parent_retriever


def test_parent_enrichment():
    """Verify candidate child chunk is enriched with parent section full text."""
    mock_candidate = {
        "chunk_id": "HR-003-CHUNK-001",
        "parent_id": "HR-003-SECTION-05",
        "text": "Brief child chunk summary...",
        "metadata": {
            "policy_id": "HR-003",
            "section_number": "5",
            "section_title": "Operating Procedure"
        }
    }

    enriched = parent_retriever.enrich_candidate_with_parent(mock_candidate)
    assert "parent_section_text" in enriched
    # Verify that parent text has content
    assert len(enriched["parent_section_text"]) > 0


def test_reranker_procedural_boost():
    """Verify reranker elevates procedural and requirement sections over scope/intro."""
    candidates = [
        {
            "chunk_id": "C1",
            "text": "1. Purpose and Scope. This policy applies to all global personnel.",
            "metadata": {"policy_id": "HR-003", "section_number": "1", "section_title": "Purpose"}
        },
        {
            "chunk_id": "C2",
            "text": "5. Operating Procedure. Employees must submit leave requests via the portal at least 5 business days in advance. Line managers must approve or reject within 48 hours.",
            "metadata": {"policy_id": "HR-003", "section_number": "5", "section_title": "Operating Procedure"}
        }
    ]

    reranked = cross_encoder_reranker.rerank(
        query="What is the leave approval procedure?",
        candidates=candidates,
        top_k=2
    )

    assert len(reranked) == 2
    # C2 should be ranked top due to procedural keyword and content match
    assert reranked[0]["chunk_id"] == "C2"
    assert reranked[0]["rerank_score"] > reranked[1]["rerank_score"]

