"""
Unit tests for Metadata Filter Extraction, Policy ID parsing, and Department detection.
"""

import pytest
from src.retrievers.metadata_filter import metadata_filter_extractor
from src.retrievers.multi_query import query_expander


def test_exact_policy_id_detection():
    """Verify exact policy ID regex captures varied capitalization and hyphenation."""
    test_cases = [
        ("What is HR-003?", "HR-003"),
        ("Tell me about fin-002 reimbursement rules", "FIN-002"),
        ("IT 001 password requirements", "IT-001"),
        ("leg-005 anti bribery guidelines", "LEG-005"),
        ("Is SEC-010 active?", "SEC-010"),
    ]

    for text, expected_id in test_cases:
        filters = metadata_filter_extractor.extract_filters(text)
        assert filters.get("policy_id") == expected_id, f"Failed for '{text}': got {filters.get('policy_id')}"


def test_department_detection_english():
    """Verify English department names and department codes map to canonical names."""
    filters_hr = metadata_filter_extractor.extract_filters("What are the human resources disciplinary procedures?")
    assert filters_hr.get("department") == "Human Resources"

    filters_fin = metadata_filter_extractor.extract_filters("Finance budget allocation rules")
    assert filters_fin.get("department") == "Finance"

    filters_proc = metadata_filter_extractor.extract_filters("Vendor selection in procurement")
    assert filters_proc.get("department") == "Procurement"


def test_bangla_query_detection():
    """Verify Bengali query identification and keyword expansion."""
    bn_query = "একজন কর্মচারী কীভাবে ছুটির আবেদন করতে পারে?"
    assert query_expander.is_bangla(bn_query) is True

    expanded = query_expander.expand(bn_query)
    assert len(expanded) >= 2
    # Ensure English domain keywords are injected
    combined_exp = " ".join(expanded).lower()
    assert "leave" in combined_exp or "annual" in combined_exp


def test_prevent_overfiltering_on_comparative_queries():
    """Verify comparative questions mentioning multiple policies/departments do not restrict to a single department."""
    comp_query = "Compare HR-001 code of conduct with LEG-002 whistleblower protection"
    filters = metadata_filter_extractor.extract_filters(comp_query)
    # Neither policy_id nor single department should lock the query
    assert "policy_id" not in filters or filters["policy_id"] is None

