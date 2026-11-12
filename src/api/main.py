"""
FastAPI Server for Enterprise Policy RAG System.
Provides RESTful endpoints for policy querying, health checks, and metadata catalog.
"""

import time
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.workflow.graph import run_policy_rag
from src.ingestion.metadata_extractor import metadata_registry
from src.retrievers.vector_retriever import chroma_retriever
from src.retrievers.bm25_retriever import bm25_retriever
from src.api.schemas import (
    AskRequest,
    AskResponse,
    SourceCitation,
    PolicyItem,
    HealthResponse
)

app = FastAPI(
    title="Enterprise Policy Hybrid RAG API",
    description="Production-grade hybrid retrieval-augmented generation for 150 enterprise policies across 10 corporate departments.",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Ensure indexes are ready on boot."""
    bm25_retriever._ensure_loaded()


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Returns system status, index statistics, and backend connectivity."""
    chunk_count = chroma_retriever.count()
    policies_count = len(metadata_registry.get_all_policies())
    bm25_ready = bm25_retriever.bm25 is not None

    return HealthResponse(
        status="healthy",
        total_indexed_chunks=chunk_count,
        total_policies=policies_count,
        chroma_db_status="connected" if chunk_count > 0 else "empty",
        bm25_status="initialized" if bm25_ready else "uninitialized"
    )


@app.post("/ask", response_model=AskResponse)
def ask_policy(request: AskRequest):
    """
    Submits an employee query to the enterprise policy knowledge base.
    Supports English and Bangla, exact policy IDs, cross-department queries,
    and automatic hallucination guardrails for out-of-scope inquiries.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    start_time = time.perf_counter()
    result = run_policy_rag(request.question, user_department=request.department, debug=bool(request.debug))
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    sources: List[SourceCitation] = []
    for c in result.get("citations", []):
        sources.append(SourceCitation(
            policy_id=c.get("policy_id", ""),
            policy_title=c.get("policy_title", ""),
            department=c.get("department", ""),
            department_code=c.get("department_code", ""),
            section_number=str(c.get("section_number", "")),
            section_title=c.get("section_title", ""),
            chunk_id=c.get("chunk_id", ""),
            source_file=c.get("source_file", ""),
            relevance_score=float(c.get("relevance_score", 0.0))
        ))

    return AskResponse(
        query=result["query"],
        answer=result["answer"],
        is_answerable=result["is_answerable"],
        confidence=result["confidence"],
        language=result["language"],
        policy_ids=result["policy_ids"],
        sources=sources,
        latency_ms=round(latency_ms, 2),
        debug_trace=result.get("debug_trace") if request.debug else None
    )


@app.get("/policies", response_model=List[PolicyItem])
def list_policies(
    department: Optional[str] = Query(None, description="Filter by department name or code (e.g. 'HR', 'Finance')")
):
    """Retrieves all 150 enterprise policy records from the policy register."""
    all_policies = metadata_registry.get_all_policies()
    items: List[PolicyItem] = []

    for pid, meta in all_policies.items():
        if department:
            d_lower = department.lower()
            if (d_lower != meta.get("department", "").lower() and
                d_lower != meta.get("department_code", "").lower()):
                continue

        items.append(PolicyItem(
            policy_id=meta.get("policy_id", pid),
            policy_title=meta.get("policy_title", ""),
            department=meta.get("department", ""),
            department_code=meta.get("department_code", ""),
            version=meta.get("version", "1.0"),
            effective_date=meta.get("effective_date", ""),
            review_date=meta.get("review_date", ""),
            status=meta.get("status", "Draft baseline"),
            classification=meta.get("classification", "Internal — Template")
        ))

    return sorted(items, key=lambda x: x.policy_id)


@app.get("/departments")
def list_departments() -> Dict[str, str]:
    """Returns the 10 corporate departments and their department codes."""
    return {
        "HR": "Human Resources",
        "IT": "Information Technology",
        "FIN": "Finance",
        "LEG": "Legal & Compliance",
        "OPS": "Operations",
        "SEC": "Corporate Security",
        "PROC": "Procurement",
        "SALES": "Sales",
        "MKT": "Marketing",
        "GOV": "Governance, Risk & Assurance"
    }

