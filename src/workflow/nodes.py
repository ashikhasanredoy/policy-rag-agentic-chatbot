"""
Workflow Nodes for LangGraph Policy RAG Pipeline.
Implements multi-stage hybrid retrieval, metadata validation, cross-encoder reranking,
context assembly, zero-hallucination evidence verification, and comprehensive debugging trace.
"""

import re
from typing import Dict, Any, List, Optional
from src.workflow.state import PolicyRAGState
from src.retrievers.metadata_filter import metadata_filter_extractor
from src.retrievers.multi_query import query_expander
from src.retrievers.bm25_retriever import bm25_retriever
from src.retrievers.vector_retriever import chroma_retriever
from src.retrievers.ensemble_retriever import ensemble_retriever
from src.retrievers.parent_retriever import parent_retriever
from src.retrievers.reranker import cross_encoder_reranker
from src.retrievers.contextual_compression import contextual_compressor
from src.retrievers.context_assembler import context_assembler
from src.retrievers.query_decomposer import query_decomposer
from src.generation.answer_generator import answer_generator


def query_analysis_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Analyzes language, policy IDs, department, and query intent."""
    query = state["query"]
    lang = "bn" if query_expander.is_bangla(query) else "en"

    filters = metadata_filter_extractor.extract_filters(query)
    if state.get("user_department") and "department" not in filters:
        filters["department"] = state["user_department"]

    detected_id = filters.get("policy_id")
    detected_dept = filters.get("department")

    decomposition = query_decomposer.decompose(query, detected_id)
    if decomposition.get("is_complex"):
        if "policy_id" in filters:
            del filters["policy_id"]
        if "department" in filters:
            del filters["department"]
        detected_id = None
        detected_dept = None

    intent_type = decomposition.get("intent_type") or query_decomposer.classify_intent(query)
    target_sections = decomposition.get("target_sections") or query_decomposer.get_target_sections_for_intent(intent_type)

    debug_trace = state.get("debug_trace", {})
    debug_trace["A. Original User Query"] = query
    debug_trace["1. Original user question"] = query
    debug_trace["2. Detected language"] = "Bangla" if lang == "bn" else "English"
    debug_trace["3. Query intent"] = intent_type
    debug_trace["4. Detected Policy IDs"] = detected_id or "None (Dynamic Discovery)"
    debug_trace["5. Query decomposition"] = decomposition
    debug_trace["9. Metadata filters"] = dict(filters)
    debug_trace["B. Query Analysis"] = {
        "language": "Bangla" if lang == "bn" else "English",
        "detected_policy_id": detected_id or "None (Broad Inquiry)",
        "detected_department": detected_dept or "None (Global Search)",
        "query_intent": intent_type,
        "target_sections": target_sections,
        "query_decomposition": decomposition,
        "query_expansion": []
    }
    debug_trace["F. Metadata Filtering"] = {
        "filters_applied": dict(filters),
        "status": "Applied" if filters else "None (Broad Retrieval)",
        "reason": f"Filter locked to {filters}" if filters else "Broad/multi-policy search permitted"
    }

    return {
        "language": lang,
        "filter_metadata": filters,
        "detected_policy_id": detected_id,
        "detected_department": detected_dept,
        "intent": intent_type,
        "target_sections": target_sections,
        "decomposition": decomposition,
        "execution_trace": {"language": lang, "extracted_filters": filters, "intent": intent_type, "target_sections": target_sections, "decomposition": decomposition},
        "debug_trace": debug_trace
    }


def query_expansion_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Generates multi-query expansions including cross-lingual variants and decomposed sub-queries."""
    query = state["query"]
    expanded = query_expander.expand(query)
    decomp = state.get("decomposition", {})
    if decomp and decomp.get("is_complex"):
        sub_qs = [sq["query"] for sq in decomp.get("sub_queries", []) if sq.get("query")]
        for sq in sub_qs:
            if sq not in expanded:
                expanded.append(sq)

    debug_trace = state.get("debug_trace", {})
    if "B. Query Analysis" in debug_trace:
        debug_trace["B. Query Analysis"]["query_expansion"] = expanded
    return {
        "expanded_queries": expanded,
        "debug_trace": debug_trace,
        "execution_trace": {**state.get("execution_trace", {}), "expanded_queries": expanded}
    }


def hybrid_retrieval_node(state: PolicyRAGState) -> Dict[str, Any]:
    """
    Runs parallel BM25 and Vector search across original and expanded queries.
    Populates exact BM25, Vector, and RRF debugging logs.
    """
    query = state["query"]
    expanded = state.get("expanded_queries") or [query]
    filters = state.get("filter_metadata")
    decomp = state.get("decomposition", {})

    # 1. Capture Raw BM25 and Vector Search Results for Debugging
    bm25_raw = bm25_retriever.search(query=query, top_k=5, filter_metadata=filters)
    vector_raw = chroma_retriever.search(query=query, top_k=5, filter_metadata=filters)

    bm25_debug = [
        {
            "ranking": i + 1,
            "policy_id": r.get("metadata", {}).get("policy_id"),
            "chunk_id": r.get("chunk_id"),
            "section": f"Sec {r.get('metadata', {}).get('section_number')}: {r.get('metadata', {}).get('section_title')}",
            "score": round(float(r.get("score", 0.0)), 4),
            "source_text": r.get("text", "")[:120].strip()
        }
        for i, r in enumerate(bm25_raw)
    ]

    vector_debug = [
        {
            "ranking": i + 1,
            "policy_id": r.get("metadata", {}).get("policy_id"),
            "chunk_id": r.get("chunk_id"),
            "section": f"Sec {r.get('metadata', {}).get('section_number')}: {r.get('metadata', {}).get('section_title')}",
            "similarity_score": round(float(r.get("score", 0.0)), 4)
        }
        for i, r in enumerate(vector_raw)
    ]

    # 2. Multi-Query Ensemble Fusion
    all_candidates: Dict[str, Dict[str, Any]] = {}
    sub_query_candidates_by_pid: Dict[str, List[Dict[str, Any]]] = {}

    # If query was decomposed into sub-queries, execute targeted sub-queries
    if decomp and decomp.get("is_complex"):
        for sq in decomp.get("sub_queries", []):
            sub_q = sq.get("query")
            target_pid = sq.get("policy_id")
            sub_filter = {"policy_id": target_pid} if target_pid else None
            sub_results = ensemble_retriever.retrieve(query=sub_q, filter_metadata=sub_filter)
            if target_pid:
                sub_query_candidates_by_pid[target_pid] = sub_results[:3]
            for r in sub_results:
                cid = r["chunk_id"]
                if cid not in all_candidates:
                    all_candidates[cid] = r
                else:
                    all_candidates[cid]["rrf_score"] = all_candidates[cid].get("rrf_score", 0.0) + r.get("rrf_score", 0.0)

    for q in expanded:
        results = ensemble_retriever.retrieve(query=q, filter_metadata=filters)
        for r in results:
            cid = r["chunk_id"]
            if cid not in all_candidates:
                all_candidates[cid] = r
            else:
                all_candidates[cid]["rrf_score"] = all_candidates[cid].get("rrf_score", 0.0) + r.get("rrf_score", 0.0)

    # Sort merged pool by cumulative RRF score
    candidates = sorted(all_candidates.values(), key=lambda x: x.get("rrf_score", 0.0), reverse=True)
    candidate_pool = candidates[:ensemble_retriever.candidate_pool]

    # Guarantee representation of all target policies from decomposition
    if decomp and decomp.get("is_complex") and decomp.get("target_policies"):
        pool_pids = set(c.get("metadata", {}).get("policy_id") for c in candidate_pool)
        for t_pid in decomp.get("target_policies", []):
            if t_pid not in pool_pids and t_pid in sub_query_candidates_by_pid:
                for chunk in sub_query_candidates_by_pid[t_pid]:
                    candidate_pool.append(chunk)

    rrf_debug = [
        {
            "combined_ranking": i + 1,
            "chunk_id": r.get("chunk_id"),
            "policy_id": r.get("metadata", {}).get("policy_id"),
            "policy_title": r.get("metadata", {}).get("policy_title"),
            "section": f"Sec {r.get('metadata', {}).get('section_number')}: {r.get('metadata', {}).get('section_title')}",
            "rrf_score": round(float(r.get("rrf_score", 0.0)), 4),
            "bm25_contribution": round(float(r.get("bm25_score", 0.0)), 4),
            "vector_contribution": round(float(r.get("vector_score", 0.0)), 4)
        }
        for i, r in enumerate(candidate_pool[:5])
    ]

    debug_trace = state.get("debug_trace", {})
    debug_trace["C. BM25 Results"] = bm25_debug
    debug_trace["D. Vector Search Results"] = vector_debug
    debug_trace["E. RRF Results"] = rrf_debug
    debug_trace["6. BM25 results"] = bm25_debug
    debug_trace["7. Vector results"] = vector_debug
    debug_trace["8. RRF results"] = rrf_debug

    return {
        "candidate_chunks": candidate_pool,
        "execution_trace": {**state.get("execution_trace", {}), "retrieved_candidate_count": len(candidate_pool)},
        "debug_trace": debug_trace
    }


def reranking_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Reranks candidate child chunks with cross-encoder sequence scoring, enforcing diversity and section targeting."""
    query = state["query"]
    candidates = state.get("candidate_chunks", [])
    expanded = state.get("expanded_queries", [])
    intent = state.get("intent")
    target_sections = state.get("target_sections")
    reranked = cross_encoder_reranker.rerank(
        query=query,
        candidates=candidates,
        expanded_queries=expanded,
        intent=intent,
        target_sections=target_sections
    )

    rerank_debug = [
        {
            "final_ranking": i + 1,
            "chunk_id": r.get("chunk_id"),
            "policy_id": r.get("metadata", {}).get("policy_id"),
            "policy_title": r.get("metadata", {}).get("policy_title"),
            "section": f"Sec {r.get('metadata', {}).get('section_number')}: {r.get('metadata', {}).get('section_title')}",
            "rerank_score": round(float(r.get("rerank_score", 0.0)), 4)
        }
        for i, r in enumerate(reranked[:8])
    ]

    # Candidate policy coverage check
    coverage_pids = list(dict.fromkeys(r.get("metadata", {}).get("policy_id") for r in reranked if r.get("metadata", {}).get("policy_id")))

    debug_trace = state.get("debug_trace", {})
    debug_trace["G. Reranking Results"] = rerank_debug
    debug_trace["9. Reranker Scores"] = rerank_debug
    debug_trace["10. Candidate policy coverage"] = coverage_pids
    debug_trace["11. Reranker scores"] = rerank_debug

    return {
        "reranked_chunks": reranked,
        "execution_trace": {**state.get("execution_trace", {}), "reranked_count": len(reranked)},
        "debug_trace": debug_trace
    }


def parent_lookup_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Enriches top reranked child chunks with parent section text hierarchy."""
    chunks = state.get("reranked_chunks", [])
    enriched = [parent_retriever.enrich_candidate_with_parent(c) for c in chunks]

    parent_expansion_debug = [
        {
            "chunk_id": c.get("chunk_id"),
            "parent_id": c.get("metadata", {}).get("parent_id"),
            "has_parent": bool(c.get("parent_text"))
        }
        for c in enriched[:6]
    ]

    debug_trace = state.get("debug_trace", {})
    debug_trace["12. Parent section expansion"] = parent_expansion_debug

    return {
        "enriched_chunks": enriched,
        "execution_trace": {**state.get("execution_trace", {}), "parent_lookup_applied": True},
        "debug_trace": debug_trace
    }


def contextual_compression_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Prunes non-essential sentences while preserving requirements, numbers, and limitations."""
    query = state["query"]
    candidates = state.get("enriched_chunks", [])
    compressed = contextual_compressor.compress_candidates(query, candidates)
    return {
        "compressed_chunks": compressed,
        "execution_trace": {**state.get("execution_trace", {}), "compression_applied": True}
    }


def context_assembly_node(state: PolicyRAGState) -> Dict[str, Any]:
    """
    Validates metadata, purges cross-policy contamination, removes duplicates,
    and organizes verified chunks into structured evidence context.
    """
    chunks = state.get("compressed_chunks", [])
    target_pid = state.get("detected_policy_id")
    decomp = state.get("decomposition", {})
    target_pids = decomp.get("target_policies") if (decomp and decomp.get("is_complex")) else None
    if target_pids:
        target_pid = None

    verified_chunks, assembled_context_str, validation_info = context_assembler.validate_and_assemble_context(
        chunks=chunks,
        target_policy_id=target_pid,
        target_policies=target_pids,
        max_chunks=8 if (decomp and decomp.get("is_complex")) else 6
    )

    debug_trace = state.get("debug_trace", {})
    debug_trace["H. Final Context Sent to LLM"] = {
        "exact_text": assembled_context_str,
        "policy_ids": list(dict.fromkeys(c.get("metadata", {}).get("policy_id") for c in verified_chunks if c.get("metadata", {}).get("policy_id"))),
        "section_references": [f"{c.get('metadata', {}).get('policy_id')}-Sec{c.get('metadata', {}).get('section_number')}" for c in verified_chunks],
        "source_filenames": list(dict.fromkeys(c.get("metadata", {}).get("source_file") for c in verified_chunks if c.get("metadata", {}).get("source_file"))),
        "validation_info": validation_info
    }
    debug_trace["10. Final Retrieved Chunks"] = [
        {
            "chunk_id": c.get("chunk_id"),
            "policy_id": c.get("metadata", {}).get("policy_id"),
            "section": f"Sec {c.get('metadata', {}).get('section_number')}: {c.get('metadata', {}).get('section_title')}"
        }
        for c in verified_chunks
    ]
    debug_trace["11. Final Context Sent to LLM"] = assembled_context_str
    debug_trace["13. Final context sent to LLM"] = assembled_context_str

    return {
        "compressed_chunks": verified_chunks,
        "assembled_context": assembled_context_str,
        "execution_trace": {**state.get("execution_trace", {}), "context_assembled": True, "validation_info": validation_info},
        "debug_trace": debug_trace
    }


def evidence_validation_node(state: PolicyRAGState) -> Dict[str, Any]:
    """
    Evaluates whether retrieved passages contain substantive policy evidence directly
    answering the user's inquiry, preventing hallucination on absent topics.
    """
    chunks = state.get("compressed_chunks", [])
    if not chunks:
        return {
            "is_answerable": False,
            "confidence_score": 0.0,
            "execution_trace": {**state.get("execution_trace", {}), "answerable": False, "reason": "No candidate chunks"}
        }

    # If query specifically targeted an exact policy ID and that policy was retrieved in top chunks
    detected_id = state.get("detected_policy_id")
    if detected_id and any(c.get("metadata", {}).get("policy_id") == detected_id for c in chunks[:3]):
        return {
            "is_answerable": True,
            "confidence_score": 0.95,
            "execution_trace": {**state.get("execution_trace", {}), "answerable": True, "reason": f"Direct policy ID match: {detected_id}"}
        }

    query = state["query"]
    is_bn = query_expander.is_bangla(query)

    STOPWORDS = {
        "what", "is", "the", "are", "can", "how", "does", "who", "under", "for",
        "in", "to", "into", "like", "their", "an", "a", "or", "and", "of", "on",
        "at", "with", "by", "from", "which", "about", "procedure", "policy",
        "process", "rules", "guidelines", "requirements", "responsibilities",
        "employee", "employees", "corporate", "company", "personal", "bring", "allowed", "provide",
        "work", "workplace", "office", "duties", "find", "all", "policies", "related",
        "tell", "explain", "give", "list", "show", "describe", "compare", "versus",
        "steps", "followed", "should", "could", "would", "activities", "many", "before", "after"
    }

    if is_bn:
        bn_to_en_digits = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
        norm_q = query.translate(bn_to_en_digits)
        percentages = re.findall(r"\b\d+%", norm_q)
        combined_text = " ".join(c.get("text", "").lower() for c in chunks[:5])
        if percentages and not any(p in combined_text for p in percentages):
            return {
                "is_answerable": False,
                "confidence_score": 0.0,
                "execution_trace": {
                    **state.get("execution_trace", {}),
                    "answerable": False,
                    "reason": f"Claimed percentages {percentages} not found in evidence"
                }
            }
    else:
        query_words = [w.lower() for w in re.findall(r"[a-zA-Z]{3,}", query) if w.lower() not in STOPWORDS]
        combined_text = " ".join(c.get("text", "").lower() for c in chunks[:5])

        # Semantic concept mapping
        CONCEPT_SYNONYMS = {
            "unethical": ["ethics", "ethical", "misconduct", "breach", "whistleblower", "violation", "investigation"],
            "advertisement": ["advertising", "campaign", "marketing", "creative", "claims"],
            "sensitive": ["confidential", "security", "safeguard", "protection", "classification", "data"],
            "protect": ["protection", "safeguards", "controls", "security", "measures"],
            "discover": ["suspect", "identify", "observe", "concern", "breach", "report"],
            "misconduct": ["disciplinary", "ethics", "conduct", "violation", "investigation", "action"],
            "disciplinary": ["discipline", "investigation", "misconduct", "consequences", "action"],
            "network": ["network", "firewall", "perimeter", "traffic", "infrastructure"],
            "resignation": ["separation", "offboarding", "departure", "exit", "settlement", "termination", "resignation"],
            "settlement": ["separation", "compensation", "payroll", "offboarding", "final", "settlement", "salary"],
            "permissions": ["access", "permission", "authorization", "accounts", "identity", "privilege", "system"],
            "transfer": ["change", "modify", "transition", "relocate", "request", "review", "transfer"],
            "evaluating": ["evaluation", "diligence", "assessment", "qualification", "screening", "supplier", "evaluating"],
            "supplier": ["vendor", "procurement", "sourcing", "supplier", "purchasing"],
            "retain": ["records", "evidence", "stored", "schedule", "retained", "retaining", "retain"],
            "harassment": ["harassment", "bullying", "conduct", "grievance", "misconduct", "reporting"]
        }

        matched_terms = []
        for w in query_words:
            w_stem = bm25_retriever.stem(w)
            synonyms = CONCEPT_SYNONYMS.get(w, []) + [w, w_stem]
            if any(re.search(rf"\b{re.escape(s)}\b", combined_text) for s in synonyms):
                matched_terms.append(w)

        coverage_ratio = len(matched_terms) / max(1, len(query_words))
        top_score = chunks[0].get("rerank_score", 0.0)

        # Refuse if no core concepts match at all
        if query_words and len(matched_terms) == 0:
            return {
                "is_answerable": False,
                "confidence_score": 0.0,
                "execution_trace": {
                    **state.get("execution_trace", {}),
                    "answerable": False,
                    "reason": f"Core concepts {query_words} not found in evidence"
                }
            }

    top_score = chunks[0].get("rerank_score", 0.0)
    is_answerable = top_score >= 0.08
    confidence = min(1.0, max(0.2, round(top_score, 2))) if is_answerable else 0.0

    return {
        "is_answerable": is_answerable,
        "confidence_score": confidence,
        "execution_trace": {**state.get("execution_trace", {}), "answerable": is_answerable, "confidence": confidence}
    }


def answer_generation_node(state: PolicyRAGState) -> Dict[str, Any]:
    """Generates the grounded answer with exact section and policy citations."""
    query = state["query"]
    chunks = state.get("compressed_chunks", [])
    is_answerable = state.get("is_answerable", True)
    confidence = state.get("confidence_score", 1.0)

    intent = state.get("intent")
    if not is_answerable:
        res = answer_generator.generate_answer(query, chunks, confidence=0.0, is_answerable=False, intent=intent)
    else:
        res = answer_generator.generate_answer(query, chunks, confidence=confidence, is_answerable=True, intent=intent)

    debug_trace = state.get("debug_trace", {})
    val = res.get("validation", {})
    debug_trace["I. Final Answer & Validation"] = {
        "generated_response": res["answer"],
        "citations": res["sources"],
        "unsupported_claims": val.get("unsupported_claims_detected", []),
        "validation_result": val
    }
    debug_trace["12. Generated Answer"] = res["answer"]
    debug_trace["13. Citation Validation Results"] = val
    debug_trace["14. Generated answer"] = res["answer"]
    debug_trace["15. Citation validation"] = val
    debug_trace["16. Unsupported claims"] = val.get("unsupported_claims_detected", [])

    return {
        "answer": res["answer"],
        "citations": res["sources"],
        "policy_ids": res["policy_ids"],
        "debug_trace": debug_trace,
        "execution_trace": {**state.get("execution_trace", {}), "generation_complete": True}
    }
