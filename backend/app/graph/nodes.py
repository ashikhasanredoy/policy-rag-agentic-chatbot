import re
from typing import Dict, Any
from backend.app.graph.state import PolicyState
from backend.app.router.intent_router import intent_router
from backend.app.router.intent_types import IntentType
from backend.app.rag.retriever import retriever
from backend.app.graders.relevance import relevance_grader
from backend.app.graders.answerability import answerability_grader
from backend.app.graders.faithfulness import faithfulness_grader
from backend.app.graders.citation import citation_extractor
from backend.app.policies.conflict import conflict_detector
from backend.app.llm.olmo import olmo_llm
from backend.app.llm.prompts import POLICY_ASSISTANT_SYSTEM_PROMPT
from backend.app.core.logging import logger

def analyze_query_node(state: PolicyState) -> Dict[str, Any]:
    """
    Unified Intent Router Node:
    Categorizes the user request into GENERAL_CHAT, POLICY_CATEGORY, POLICY_LIST, POLICY_QUERY, or OUT_OF_SCOPE.
    """
    query = state.get("query", "")
    logger.info(f"Node [AnalyzeQuery]: Routing query '{query}'")

    intent_type, category_info = intent_router.route(query)

    synonyms = {
        r"\bhr\b": "human resources annual leave time off remote work",
        r"\bwfh\b": "work from home remote work",
        r"\bpto\b": "paid time off annual leave vacation",
        r"\bsick leave\b": "medical leave health leave",
        r"\bexp\b": "expense reimbursement per diem",
        r"\bbyod\b": "bring your own device personal mobile device",
        r"\bdsar\b": "data subject access request gdpr ccpa",
        r"\bnda\b": "non-disclosure confidentiality agreement",
    }

    rewritten = query.lower()
    for pattern, replacement in synonyms.items():
        rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

    return {
        "intent_type": intent_type.value,
        "intent": intent_type.value.lower(),
        "category_info": category_info,
        "search_query": rewritten,
        "normalized_keywords": rewritten.split(),
        "execution_trace": {
            **state.get("execution_trace", {}),
            "intent_type": intent_type.value,
            "search_query": rewritten
        }
    }

def general_chat_node(state: PolicyState) -> Dict[str, Any]:
    """Handles everyday conversation, greetings, and basic small talk without RAG overhead."""
    query = state.get("query", "").strip().lower()
    logger.info("Node [GeneralChat]: Handling general conversation")

    if any(k in query for k in ["how are you", "how's it going", "how are you doing"]):
        answer = "I'm doing well, thank you! 😊 How can I help you with company policies today?"
    elif any(k in query for k in ["thank", "thx", "appreciate"]):
        answer = "You're very welcome! Let me know if you need help with anything else."
    elif any(k in query for k in ["bye", "goodbye", "see you", "have a good day"]):
        answer = "Goodbye! Have a great and productive day ahead. Reach out whenever you need policy assistance."
    elif any(k in query for k in ["who are you", "what are you"]):
        answer = (
            "I'm your Enterprise Policy Assistant! 🏢\n\n"
            "I provide accurate, policy-grounded answers across HR, Leave, Remote Work, Travel & Expenses, "
            "IT Security, Benefits & Perks, and Code of Conduct with direct source citations."
        )
    elif any(k in query for k in ["give me some question", "give me questions", "sample question", "example question", "suggest some question", "suggest question", "what questions"]):
        answer = (
            "Here are some popular questions you can ask me across company policies:\n\n"
            "🌴 **HR & Leave**\n"
            "• *\"How many annual leave days do full-time employees get?\"*\n"
            "• *\"What is the carryover policy for unused annual leave?\"*\n\n"
            "🏡 **Remote Work**\n"
            "• *\"How many days per week can I work from home?\"*\n"
            "• *\"What are the mandatory core hours for remote employees?\"*\n\n"
            "✈️ **Travel & Expenses**\n"
            "• *\"What is the daily meal per diem for business travel?\"*\n"
            "• *\"What is the maximum allowed hotel room rate per night?\"*\n\n"
            "🎓 **Benefits & Perks**\n"
            "• *\"Does the company offer tuition assistance or reimbursement?\"*\n"
            "• *\"What is the 401(k) company matching percentage?\"*\n\n"
            "🔒 **IT & Security**\n"
            "• *\"What is the minimum required password length and complexity?\"*\n"
            "• *\"What is the deadline to report a lost or stolen laptop?\"*\n\n"
            "Feel free to click or type any question!"
        )
    elif any(k in query for k in ["what can you do", "what do you do", "help", "how can you help"]):
        answer = (
            "I can help you find verified information from active company policies, including:\n"
            "• **HR & Leave** (Annual vacation, sick days, parental leave)\n"
            "• **Remote Work** (Hybrid schedules, core hours, home office equipment)\n"
            "• **Travel & Expenses** (Meal per diem, airfare, hotel lodging, reimbursement)\n"
            "• **IT & Security** (Password rules, MFA, VPN, device security)\n"
            "• **Benefits & Perks** (401(k) retirement matching, tuition reimbursement)\n"
            "• **Code of Conduct** (Gifts, anti-harassment, ethics reporting)\n\n"
            "What policy question can I help you with today?"
        )
    else:
        answer = (
            "Hello! 👋 I'm your Enterprise Policy Assistant.\n\n"
            "How can I help you today? You can ask me any question about company policies, such as annual leave, "
            "remote work guidelines, travel meal allowances, or benefits."
        )

    return {
        "answer": answer,
        "answerable": True,
        "confidence": 1.0,
        "citations": [],
        "relevant_documents": [],
        "status": "answered",
        "execution_trace": {
            **state.get("execution_trace", {}),
            "handler": "general_chat_node"
        }
    }

def policy_category_node(state: PolicyState) -> Dict[str, Any]:
    """Handles broad policy category overviews and guides the user to specific inquiries."""
    category_info = state.get("category_info")
    logger.info("Node [PolicyCategory]: Providing category orientation")

    if category_info:
        name = category_info.get("name", "Company Policy")
        desc = category_info.get("description", "")
        examples = category_info.get("examples", [])
        
        example_bullets = "\n".join([f"• \"{ex}\"" for ex in examples])
        answer = (
            f"Sure! 😊 Here is an overview of **{name}**:\n\n"
            f"{desc}\n\n"
            f"**What specifically would you like to know?** For example, you can ask:\n"
            f"{example_bullets}"
        )
    else:
        answer = (
            "Sure! 😊 We have comprehensive company policies covering:\n"
            "• **HR & Leave** (20 days annual vacation, 5 days rollover, sick days)\n"
            "• **Remote Work** (Up to 2 days/week WFH, core hours 10 AM - 4 PM)\n"
            "• **Travel & Expenses** ($75/day meal per diem, flight & hotel rules)\n"
            "• **IT & Security** (14+ char passwords, MFA, clean desk, VPN)\n"
            "• **Benefits & Perks** (401k match, $5,250 tuition reimbursement)\n"
            "• **Code of Conduct** ($100 gift limit, anti-harassment, whistleblower)\n\n"
            "What specific topic or rule would you like to know about?"
        )

    return {
        "answer": answer,
        "answerable": True,
        "confidence": 1.0,
        "citations": [],
        "relevant_documents": [],
        "status": "answered",
        "execution_trace": {
            **state.get("execution_trace", {}),
            "handler": "policy_category_node"
        }
    }

def policy_list_node(state: PolicyState) -> Dict[str, Any]:
    """Returns the complete list of active policies indexed in the system."""
    logger.info("Node [PolicyList]: Listing active policies")
    answer = (
        "Here are the active company policies currently indexed:\n\n"
        "1. 📋 **Annual Leave and Absence Management Policy** (POL-HR-001)\n"
        "2. 🏠 **Remote, Hybrid Workplace, and Telecommuting Policy** (POL-HR-002)\n"
        "3. ✈️ **Business Travel, Expense Reimbursement, and Corporate Card Policy** (POL-FIN-003)\n"
        "4. 🔒 **Information Security and Acceptable Use Policy** (POL-SEC-004)\n"
        "5. 💻 **BYOD and IT Endpoint Security Policy** (POL-IT-005)\n"
        "6. 🤝 **Code of Conduct, Ethics, and Anti-Harassment Policy** (POL-OPS-006)\n"
        "7. 🎁 **Employee Benefits and Perks Policy** (POL-HR-007)\n\n"
        "Feel free to ask any question regarding these policies!"
    )
    return {
        "answer": answer,
        "answerable": True,
        "confidence": 1.0,
        "citations": [],
        "relevant_documents": [],
        "status": "answered",
        "execution_trace": {
            **state.get("execution_trace", {}),
            "handler": "policy_list_node"
        }
    }

def out_of_scope_node(state: PolicyState) -> Dict[str, Any]:
    """Respectfully informs the user that out-of-domain requests are outside enterprise policy scope."""
    logger.info("Node [OutOfScope]: Refusing out-of-scope query")
    answer = (
        "I'm an enterprise assistant designed specifically to help with **company policies and workplace guidelines**.\n\n"
        "I don't have access to external real-time data (like weather, news, or general web search). "
        "Please feel free to ask me anything about company HR, leave, remote work, expenses, security, or benefits!"
    )
    return {
        "answer": answer,
        "answerable": True,
        "confidence": 1.0,
        "citations": [],
        "relevant_documents": [],
        "status": "answered",
        "execution_trace": {
            **state.get("execution_trace", {}),
            "handler": "out_of_scope_node"
        }
    }

def retrieve_node(state: PolicyState) -> Dict[str, Any]:
    search_query = state.get("search_query", state.get("query", ""))
    cat_filter = state.get("category_filter")
    dept_filter = state.get("department_filter")

    logger.info(f"Node [Retrieve]: Executing hybrid search for '{search_query}'")
    docs = retriever.retrieve(
        query=search_query,
        category=cat_filter,
        department=dept_filter,
        status="active"
    )

    has_conflict, conflict_msg, _ = conflict_detector.detect_conflicts(docs)

    return {
        "retrieved_documents": docs,
        "conflict_detected": has_conflict,
        "conflict_details": conflict_msg if has_conflict else None,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "retrieved_count": len(docs),
            "conflict_detected": has_conflict
        }
    }

def grade_relevance_node(state: PolicyState) -> Dict[str, Any]:
    query = state.get("query", "")
    docs = state.get("retrieved_documents", [])

    logger.info(f"Node [GradeRelevance]: Grading {len(docs)} retrieved documents")
    relevant_docs, avg_score = relevance_grader.filter_relevant(query, docs)

    passed = len(relevant_docs) > 0

    return {
        "relevant_documents": relevant_docs,
        "relevance_passed": passed,
        "relevance_score": avg_score,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "relevance_passed": passed,
            "relevant_count": len(relevant_docs),
            "relevance_score": round(avg_score, 3)
        }
    }

def grade_answerability_node(state: PolicyState) -> Dict[str, Any]:
    query = state.get("query", "")
    docs = state.get("relevant_documents", [])

    logger.info(f"Node [GradeAnswerability]: Evaluating strict answerability")
    is_answerable, confidence, reason = answerability_grader.grade(query, docs)

    return {
        "answerable": is_answerable,
        "answerability_score": confidence,
        "answerability_reason": reason,
        "confidence": confidence,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "answerability_passed": is_answerable,
            "answerability_score": round(confidence, 3),
            "answerability_reason": reason
        }
    }

def generate_node(state: PolicyState) -> Dict[str, Any]:
    query = state.get("query", "")
    docs = state.get("relevant_documents", [])
    logger.info("Node [Generate]: Generating policy-grounded answer via OLMo")

    context_str = "\n\n".join([
        f"[Source {i+1}: {d.get('policy_name', 'Policy')} (Section: {d.get('section', 'General')})]\n{d.get('text', '')}"
        for i, d in enumerate(docs)
    ])

    user_prompt = (
        f"Answer the employee's question using ONLY the provided policy context.\n\n"
        f"Question: {query}\n\n"
        f"Policy Evidence:\n{context_str}\n\n"
        f"Answer with clear facts and cite the relevant section numbers."
    )

    llm_response = olmo_llm.generate(prompt=user_prompt, system_prompt=POLICY_ASSISTANT_SYSTEM_PROMPT)
    citations = citation_extractor.extract_citations(docs)

    return {
        "answer": llm_response,
        "answerable": True,
        "confidence": state.get("confidence", 1.0),
        "citations": citations,
        "status": "answered",
        "execution_trace": {
            **state.get("execution_trace", {}),
            "answer_generated": True,
            "citations_count": len(citations)
        }
    }

def grade_faithfulness_node(state: PolicyState) -> Dict[str, Any]:
    answer = state.get("answer", "")
    docs = state.get("relevant_documents", [])

    logger.info("Node [GradeFaithfulness]: Verifying answer faithfulness against sources")
    is_faithful, score, unsupported = faithfulness_grader.grade(answer, docs)

    return {
        "faithfulness_passed": is_faithful,
        "faithfulness_score": score,
        "unsupported_claims": unsupported,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "faithfulness_passed": is_faithful,
            "faithfulness_score": round(score, 3),
            "unsupported_count": len(unsupported)
        }
    }

def retry_query_node(state: PolicyState) -> Dict[str, Any]:
    retries = state.get("retry_count", 0) + 1
    query = state.get("query", "")
    logger.info(f"Node [RetryQuery]: Retrying query generation (attempt {retries})")

    words = [w for w in query.split() if len(w) > 3]
    broadened = " ".join(words)

    return {
        "retry_count": retries,
        "search_query": broadened,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "retry_attempt": retries
        }
    }

def abstain_node(state: PolicyState) -> Dict[str, Any]:
    query = state.get("query", "")
    reason = state.get("answerability_reason", "No sufficient policy evidence found.")
    conflict = state.get("conflict_detected", False)
    conflict_details = state.get("conflict_details")

    logger.info("Node [Abstain]: Generating deterministic abstention response")

    if conflict and conflict_details:
        answer = (
            f"⚠️ **Policy Conflict Detected**: {conflict_details}\n\n"
            "I found contradictory rules across active company policy documents. "
            "To prevent providing incorrect guidance, I cannot give a definitive rule. "
            "Please consult the Policy Compliance Officer or HR representative for clarification."
        )
        status = "conflict_detected"
    else:
        answer = (
            f"ℹ️ I couldn't find information regarding your request in the active company policies.\n\n"
            f"*Reason:* {reason}\n\n"
            "To ensure compliance and accuracy, I do not generate unverified company rules. "
            "Please check with your department manager or Human Resources."
        )
        status = "abstained_not_found"

    return {
        "answer": answer,
        "answerable": False,
        "confidence": 0.0,
        "citations": [],
        "status": status,
        "execution_trace": {
            **state.get("execution_trace", {}),
            "abstain_status": status,
            "abstain_reason": reason
        }
    }
