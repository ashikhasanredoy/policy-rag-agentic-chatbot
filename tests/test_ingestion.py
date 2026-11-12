"""
Unit tests for Document Ingestion, Structured DOCX Extraction, and Metadata Registry.
"""

from pathlib import Path
import pytest
from src.config.settings import settings
from src.ingestion.docx_loader import DocxPolicyLoader
from src.ingestion.metadata_extractor import metadata_registry
from src.ingestion.document_loader import unified_loader
from src.ingestion.chunking import parent_child_chunker


def test_metadata_registry_loaded():
    """Verify Policy_Register.csv loaded 150 unique policies across all 10 departments."""
    policies = metadata_registry.get_all_policies()
    assert len(policies) == 150, f"Expected 150 policies, got {len(policies)}"

    # Check that canonical policies exist
    hr_003 = metadata_registry.get_policy("HR-003")
    assert hr_003 is not None
    assert hr_003["department_code"] == "HR"
    assert "Leave" in hr_003["policy_title"]


def test_docx_parsing_structure():
    """Verify DOCX parser extracts sections, headings, and metadata correctly."""
    sample_file = settings.ORIGINAL_DOCS_DIR / "HR" / "HR-003_Leave_Management.docx"
    assert sample_file.exists(), f"Sample file not found: {sample_file}"

    parsed = DocxPolicyLoader.load(sample_file)
    assert parsed["metadata"]["policy_id"] == "HR-003"
    assert len(parsed["sections"]) >= 5, f"Expected at least 5 sections, got {len(parsed['sections'])}"

    # Check for standard sections
    section_titles = [s["section_title"].lower() for s in parsed["sections"]]
    assert any("purpose" in t for t in section_titles)
    assert any("procedure" in t or "operating" in t for t in section_titles)


def test_parent_child_chunking():
    """Verify Parent-Child section chunker preserves parent ID linkages and standard 12 sections."""
    sample_file = settings.ORIGINAL_DOCS_DIR / "FIN" / "FIN-002_Expense_Reimbursement.docx"
    assert sample_file.exists(), f"Sample file not found: {sample_file}"
    parsed_policy = unified_loader.load_policy(sample_file)

    child_chunks, parent_sections = parent_child_chunker.chunk_policy(parsed_policy)

    assert len(parent_sections) > 0
    assert len(child_chunks) >= len(parent_sections)

    # Validate parent-child bi-directional linkage
    for chunk in child_chunks:
        assert chunk.parent_id in parent_sections, f"Orphan chunk found: {chunk.chunk_id}"
        assert chunk.metadata["policy_id"] == "FIN-002"
        assert chunk.metadata["department_code"] == "FIN"
