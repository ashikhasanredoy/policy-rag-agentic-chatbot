from typing import TypedDict, List, Dict, Any, Optional

class PolicyState(TypedDict):
    # User Input
    query: str
    department_filter: Optional[str]
    category_filter: Optional[str]

    # Query Analysis & Routing
    intent: str
    intent_type: str  # GENERAL_CHAT, POLICY_CATEGORY, POLICY_LIST, POLICY_QUERY, OUT_OF_SCOPE
    category_info: Optional[Dict[str, Any]]
    normalized_keywords: List[str]
    search_query: str

    # Retrieval
    retrieved_documents: List[Dict[str, Any]]
    relevant_documents: List[Dict[str, Any]]

    # Grading & Guardrails
    relevance_score: float
    relevance_passed: bool
    answerable: bool
    answerability_score: float
    answerability_reason: str
    conflict_detected: bool
    conflict_details: Optional[str]

    # Generation & Faithfulness
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    faithfulness_score: float
    faithfulness_passed: bool
    unsupported_claims: List[str]

    # Agent Loop Control
    retry_count: int
    max_retries: int
    status: str  # 'answered', 'abstained_not_found', 'abstained_unfaithful', 'conflict_detected'
    execution_trace: Dict[str, Any]
