from langgraph.graph import StateGraph, END
from backend.app.graph.state import PolicyState
from backend.app.graph.nodes import (
    analyze_query_node,
    general_chat_node,
    policy_category_node,
    policy_list_node,
    out_of_scope_node,
    retrieve_node,
    grade_relevance_node,
    grade_answerability_node,
    generate_node,
    grade_faithfulness_node,
    retry_query_node,
    abstain_node
)
from backend.app.graph.edges import (
    route_after_analyze,
    route_after_relevance,
    route_after_answerability,
    route_after_faithfulness
)
from backend.app.core.config import settings

def build_policy_rag_graph():
    workflow = StateGraph(PolicyState)

    # 1. Add All Graph Nodes
    workflow.add_node("analyze_query", analyze_query_node)
    workflow.add_node("general_chat", general_chat_node)
    workflow.add_node("policy_category", policy_category_node)
    workflow.add_node("policy_list", policy_list_node)
    workflow.add_node("out_of_scope", out_of_scope_node)
    
    # RAG Engine Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_relevance", grade_relevance_node)
    workflow.add_node("grade_answerability", grade_answerability_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("grade_faithfulness", grade_faithfulness_node)
    workflow.add_node("retry_query", retry_query_node)
    workflow.add_node("abstain", abstain_node)

    # 2. Add Graph Entry Point
    workflow.set_entry_point("analyze_query")

    # Intent Router Conditional Edge
    workflow.add_conditional_edges(
        "analyze_query",
        route_after_analyze,
        {
            "general_chat": "general_chat",
            "policy_category": "policy_category",
            "policy_list": "policy_list",
            "out_of_scope": "out_of_scope",
            "retrieve": "retrieve"
        }
    )

    # Direct Terminal Edges for Non-RAG Intents
    workflow.add_edge("general_chat", END)
    workflow.add_edge("policy_category", END)
    workflow.add_edge("policy_list", END)
    workflow.add_edge("out_of_scope", END)

    # RAG Pipeline Edges
    workflow.add_edge("retrieve", "grade_relevance")

    # Relevance Conditional Edge
    workflow.add_conditional_edges(
        "grade_relevance",
        route_after_relevance,
        {
            "grade_answerability": "grade_answerability",
            "abstain": "abstain"
        }
    )

    # Answerability Conditional Edge ("No evidence -> No answer")
    workflow.add_conditional_edges(
        "grade_answerability",
        route_after_answerability,
        {
            "generate": "generate",
            "abstain": "abstain"
        }
    )

    # Faithfulness Check after Generation
    workflow.add_edge("generate", "grade_faithfulness")

    # Faithfulness Conditional Edge
    workflow.add_conditional_edges(
        "grade_faithfulness",
        route_after_faithfulness,
        {
            "end": END,
            "retry_query": "retry_query",
            "abstain": "abstain"
        }
    )

    # Retry loops back to retrieval
    workflow.add_edge("retry_query", "retrieve")

    # Abstain concludes the execution
    workflow.add_edge("abstain", END)

    return workflow.compile()

policy_rag_agent = build_policy_rag_graph()
