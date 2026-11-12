"""
Unit tests for Citation Generation and Auditable Attribution.
"""

import pytest
from src.generation.citations import citation_mapper


def test_citation_mapping():
    """Verify CitationMapper extracts structured citation metadata from chunks."""
    chunks = [
        {
            "chunk_id": "HR-003-CHUNK-002",
            "text": "Employees must submit leave requests via HR portal.",
            "rerank_score": 0.92,
            "metadata": {
                "policy_id": "HR-003",
                "policy_title": "Leave Management",
                "department": "Human Resources",
                "department_code": "HR",
                "section_number": "5",
                "section_title": "Operating Procedure",
                "source_file": "Human Resources/HR-003_Leave_Management.docx"
            }
        }
    ]

    citations = citation_mapper.create_citations(chunks)
    assert len(citations) == 1
    c = citations[0]
    assert c["policy_id"] == "HR-003"
    assert c["department"] == "Human Resources"
    assert c["section_number"] == "5"
    assert c["section_title"] == "Operating Procedure"
    assert c["relevance_score"] == 0.92

    formatted = citation_mapper.format_citations_markdown(citations)
    assert "HR-003" in formatted
    assert "Operating Procedure" in formatted

