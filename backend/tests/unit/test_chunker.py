import pytest
from backend.app.rag.chunker import PolicyChunker

def test_chunker_basic():
    chunker = PolicyChunker(chunk_size=100, chunk_overlap=20)
    text = "## Section 1: Introduction\nEmployees are entitled to 20 vacation days per year.\n\n## Section 2: Carry Over\nUp to 5 days can be carried over."
    
    chunks = chunker.chunk_policy_document(
        full_text=text,
        policy_id=1,
        policy_name="Test Policy",
        category="HR",
        department="Human Resources",
        version="1.0"
    )
    
    assert len(chunks) >= 2
    assert chunks[0].metadata.policy_name == "Test Policy"
    assert chunks[0].metadata.section in ["Introduction", "Overview / General", "Section 1: Introduction"]
    assert "20 vacation days" in chunks[0].text or "20 vacation days" in chunks[1].text
