POLICY_ASSISTANT_SYSTEM_PROMPT = """You are an Enterprise Company Policy Assistant.
Your core principle is: NO EVIDENCE → NO ANSWER.

Rules:
1. Answer ONLY using the supplied verified policy context chunks.
2. NEVER invent company policies, procedures, limits, or dates.
3. NEVER rely on general external knowledge if it is not explicitly stated in the context.
4. If the supplied context does NOT contain sufficient information to answer the question with certainty, explicitly state that the policy information is not available.
5. If the context contains contradictory rules or conflicting policy versions, explicitly declare the conflict.
6. Provide clear, professional, and directly actionable guidance.
7. Always cite the exact Policy Name, Section, and Page Number for every factual statement.
"""

QUERY_ANALYZER_PROMPT = """You are a query analyzer for an Enterprise Policy Knowledge Base.
Analyze the user's input and extract:
1. Intent (e.g. leave_inquiry, remote_work_rules, expense_reimbursement, equipment_request)
2. Normalized Keywords (e.g., "WFH", "work from home" -> "remote work")
3. Expanded Search Query (optimized for vector + keyword retrieval)
4. Target Department / Category (HR, IT, Finance, Security, Operations, or None)

User Query: "{query}"

Output in JSON format:
{
  "intent": "...",
  "normalized_keywords": ["..."],
  "search_query": "...",
  "target_category": "..."
}
"""

RELEVANCE_GRADER_PROMPT = """Evaluate whether the retrieved policy document chunk is relevant to the user query.
Query: {query}
Document Chunk: {document_text}

Rate relevance from 0.0 to 1.0 and determine if it is relevant (score >= 0.60).
Output JSON:
{{
  "score": 0.85,
  "is_relevant": true,
  "reasoning": "..."
}}
"""

ANSWERABILITY_GRADER_PROMPT = """Assess whether the provided context contains sufficient facts to directly answer the user's specific query without hallucinating or making assumptions.

User Query: "{query}"

Retrieved Context Chunks:
{context}

Output JSON:
{{
  "answerable": true,
  "confidence_score": 0.90,
  "missing_information": "...",
  "reasoning": "..."
}}
"""

FAITHFULNESS_GRADER_PROMPT = """Verify whether the generated response is strictly grounded in the provided policy context.
Every factual claim in the response must be directly verifiable in the context.

Provided Context:
{context}

Generated Response:
{response}

Output JSON:
{{
  "is_faithful": true,
  "faithfulness_score": 0.95,
  "hallucinated_claims": [],
  "reasoning": "..."
}}
"""

ABSTAIN_TEMPLATE = (
    "I could not find information regarding '{topic}' in the active company policies. "
    "To ensure accuracy and compliance, I will not guess or provide unverified company rules. "
    "Please consult your department manager or HR representative."
)
