from typing import Literal
from backend.app.graph.state import PolicyState
from backend.app.router.intent_types import IntentType

def route_after_analyze(state: PolicyState) -> Literal["general_chat", "policy_category", "policy_list", "out_of_scope", "retrieve"]:
    """
    Routes based on IntentRouter classification:
    - GENERAL_CHAT -> general_chat node
    - POLICY_CATEGORY -> policy_category node
    - POLICY_LIST -> policy_list node
    - OUT_OF_SCOPE -> out_of_scope node
    - POLICY_QUERY -> retrieve node (Hybrid RAG)
    """
    intent_type = state.get("intent_type", IntentType.POLICY_QUERY.value)

    if intent_type == IntentType.GENERAL_CHAT.value:
        return "general_chat"
    elif intent_type == IntentType.POLICY_CATEGORY.value:
        return "policy_category"
    elif intent_type == IntentType.POLICY_LIST.value:
        return "policy_list"
    elif intent_type == IntentType.OUT_OF_SCOPE.value:
        return "out_of_scope"
    else:
        return "retrieve"

def route_after_relevance(state: PolicyState) -> Literal["grade_answerability", "abstain"]:
    """Routes to answerability check if relevant documents exist; otherwise abstains."""
    if state.get("relevance_passed", False) and state.get("relevant_documents"):
        return "grade_answerability"
    return "abstain"

def route_after_answerability(state: PolicyState) -> Literal["generate", "abstain"]:
    """
    Core 'No evidence -> No answer' router.
    Routes to OLMo generate only if answerable; otherwise routes straight to abstain.
    """
    if state.get("answerable", False):
        return "generate"
    return "abstain"

def route_after_faithfulness(state: PolicyState) -> Literal["end", "retry_query", "abstain"]:
    """
    Routes to end if answer is faithful to evidence.
    If unfaithful and retries remain, retries search. Otherwise abstains.
    """
    if state.get("faithfulness_passed", True):
        return "end"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count < max_retries:
        return "retry_query"
    return "abstain"
