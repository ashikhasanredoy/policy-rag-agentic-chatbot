"""
LangGraph Workflow Graph Construction for Enterprise Policy RAG.
Orchestrates nodes into a state machine with strict evidence validation and debugging trace.
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from src.workflow.state import PolicyRAGState
from src.workflow.nodes import (
    query_analysis_node,
    query_expansion_node,
    hybrid_retrieval_node,
    parent_lookup_node,
    reranking_node,
    contextual_compression_node,
    context_assembly_node,
    evidence_validation_node,
    answer_generation_node,
)


def create_policy_rag_graph() -> StateGraph:
    """Builds the compiled LangGraph workflow for Enterprise Policy RAG."""
    workflow = StateGraph(PolicyRAGState)

    # Register Nodes
    workflow.add_node("query_analysis", query_analysis_node)
    workflow.add_node("query_expansion", query_expansion_node)
    workflow.add_node("hybrid_retrieval", hybrid_retrieval_node)
    workflow.add_node("parent_lookup", parent_lookup_node)
    workflow.add_node("reranking", reranking_node)
    workflow.add_node("contextual_compression", contextual_compression_node)
    workflow.add_node("context_assembly", context_assembly_node)
    workflow.add_node("evidence_validation", evidence_validation_node)
    workflow.add_node("answer_generation", answer_generation_node)

    # Set Entry Point
    workflow.set_entry_point("query_analysis")

    # Connect Edges matching Phase 10 verified sequence:
    # Hybrid Retrieval -> Child Chunk Reranking -> Parent Section Expansion -> Contextual Compression -> Context Assembly
    workflow.add_edge("query_analysis", "query_expansion")
    workflow.add_edge("query_expansion", "hybrid_retrieval")
    workflow.add_edge("hybrid_retrieval", "reranking")
    workflow.add_edge("reranking", "parent_lookup")
    workflow.add_edge("parent_lookup", "contextual_compression")
    workflow.add_edge("contextual_compression", "context_assembly")
    workflow.add_edge("context_assembly", "evidence_validation")
    workflow.add_edge("evidence_validation", "answer_generation")
    workflow.add_edge("answer_generation", END)

    return workflow.compile()


# Singleton compiled graph instance
rag_app = create_policy_rag_graph()


def run_policy_rag(
    query: str,
    user_department: Optional[str] = None,
    debug: bool = False
) -> Dict[str, Any]:
    """Convenience helper to invoke the LangGraph pipeline with a user question."""
    initial_state: PolicyRAGState = {
        "query": query,
        "user_department": user_department,
        "debug_mode": debug,
        "language": "en",
        "intent": "policy_query",
        "detected_policy_id": None,
        "detected_department": None,
        "filter_metadata": {},
        "expanded_queries": [],
        "candidate_chunks": [],
        "enriched_chunks": [],
        "reranked_chunks": [],
        "compressed_chunks": [],
        "assembled_context": "",
        "is_answerable": True,
        "confidence_score": 1.0,
        "answer": "",
        "citations": [],
        "policy_ids": [],
        "execution_trace": {},
        "debug_trace": {}
    }

    result = rag_app.invoke(initial_state)
    return {
        "query": query,
        "answer": result.get("answer", ""),
        "is_answerable": result.get("is_answerable", True),
        "confidence": result.get("confidence_score", 1.0),
        "citations": result.get("citations", []),
        "policy_ids": result.get("policy_ids", []),
        "language": result.get("language", "en"),
        "trace": result.get("execution_trace", {}),
        "debug_trace": result.get("debug_trace", {})
    }
