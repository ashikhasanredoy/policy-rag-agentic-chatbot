import pytest
from backend.app.rag.bm25 import BM25Index

def test_bm25_search():
    index = BM25Index()
    docs = [
        {"text": "Employees get twenty annual leave days every single year.", "metadata": {"status": "active", "policy_name": "Annual Leave"}},
        {"text": "Corporate travel meal per diem is seventy-five dollars.", "metadata": {"status": "active", "policy_name": "Travel"}},
        {"text": "Remote work is permitted up to two days weekly.", "metadata": {"status": "active", "policy_name": "Remote Work"}}
    ]
    index.fit(docs)

    results = index.search("annual leave days", top_k=2)
    assert len(results) > 0
    top_doc, score = results[0]
    assert "annual leave" in top_doc["text"].lower()
    assert top_doc["metadata"]["policy_name"] == "Annual Leave"
