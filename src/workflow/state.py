"""
LangGraph State Definition for Enterprise Policy RAG Workflow.
Includes debugging trace and validation metadata.
"""

from typing import List, Dict, Any, Optional, TypedDict


class PolicyRAGState(TypedDict, total=False):
    # Input
    query: str
    user_department: Optional[str]
    debug_mode: bool

    # Analysis & Filtering
    language: str
    intent: str
    detected_policy_id: Optional[str]
    detected_department: Optional[str]
    filter_metadata: Dict[str, Any]
    decomposition: Dict[str, Any]
    expanded_queries: List[str]

    # Retrieval
    candidate_chunks: List[Dict[str, Any]]
    enriched_chunks: List[Dict[str, Any]]
    reranked_chunks: List[Dict[str, Any]]
    compressed_chunks: List[Dict[str, Any]]
    assembled_context: str

    # Evaluation & Output
    is_answerable: bool
    confidence_score: float
    answer: str
    citations: List[Dict[str, Any]]
    policy_ids: List[str]
    execution_trace: Dict[str, Any]
    debug_trace: Dict[str, Any]
