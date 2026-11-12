"""
Pydantic Schemas for Enterprise Policy RAG API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., description="The user question in English or Bengali (Bangla).", example="What is the procedure for employee expense reimbursement?")
    department: Optional[str] = Field(None, description="Optional department filter (e.g. 'Human Resources', 'HR', 'Finance').", example="Finance")
    debug: Optional[bool] = Field(False, description="Enable comprehensive 11-point Retrieval Debugging Mode trace.", example=False)


class SourceCitation(BaseModel):
    policy_id: str
    policy_title: str
    department: str
    department_code: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    chunk_id: Optional[str] = None
    source_file: Optional[str] = None
    relevance_score: float = 0.0


class AskResponse(BaseModel):
    query: str
    answer: str
    is_answerable: bool
    confidence: float
    language: str
    policy_ids: List[str]
    sources: List[SourceCitation]
    latency_ms: float
    debug_trace: Optional[Dict[str, Any]] = None


class PolicyItem(BaseModel):
    policy_id: str
    policy_title: str
    department: str
    department_code: str
    version: str
    effective_date: str
    review_date: str
    status: str
    classification: str


class HealthResponse(BaseModel):
    status: str
    total_indexed_chunks: int
    total_policies: int
    chroma_db_status: str
    bm25_status: str
