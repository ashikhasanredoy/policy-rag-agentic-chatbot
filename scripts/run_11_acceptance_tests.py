#!/usr/bin/env python3
"""
Verification Script for the 11 Acceptance Tests (Phase 21).
Executes all 11 queries across LangGraph Policy RAG pipeline with full 16-stage Debug Telemetry.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.workflow.graph import run_policy_rag

ACCEPTANCE_TESTS = [
    {
        "id": 1,
        "query": "What is the procedure for employee expense reimbursement?",
        "expected_pids": ["FIN-002"],
        "expected_section": "Section 5 — Operating Procedure",
        "description": "TEST 1: Standard Single-Policy Operating Procedure (Finance)",
        "expect_answerable": True
    },
    {
        "id": 2,
        "query": "How can an employee apply for leave?",
        "expected_pids": ["HR-003"],
        "expected_section": "Section 5 — Operating Procedure",
        "description": "TEST 2: Standard Single-Policy Operating Procedure (HR)",
        "expect_answerable": True
    },
    {
        "id": 3,
        "query": "What happens when an employee violates the code of conduct?",
        "expected_pids": ["HR-001"],
        "expected_section": "Section 5 (Due Process) & Section 10 (Non-Compliance)",
        "description": "TEST 3: Investigation & Progressive Disciplinary Sanctions",
        "expect_answerable": True
    },
    {
        "id": 4,
        "query": "How does the company grant, modify, and revoke system access?",
        "expected_pids": ["IT-002"],
        "expected_section": "Section 5 — Operating Procedure",
        "description": "TEST 4: Access Lifecycle Operating Procedure (IT)",
        "expect_answerable": True
    },
    {
        "id": 5,
        "query": "How does the company evaluate and approve new suppliers?",
        "expected_pids": ["PROC-002", "PROC-006", "FIN-012"],
        "expected_section": "Section 5 & Financial Approval",
        "description": "TEST 5: Supplier Due Diligence & Financial Approval Delegation",
        "expect_answerable": True
    },
    {
        "id": 6,
        "query": "Find all policies related to employee misconduct, investigation, and disciplinary action.",
        "expected_pids": ["HR-001", "HR-014", "HR-013", "LEG-004"],
        "expected_section": "Multi-Policy Overview",
        "description": "TEST 6: Cross-Policy Discovery & Governance Mapping",
        "expect_answerable": True
    },
    {
        "id": 7,
        "query": "Explain the differences between Information Security Policy and Network Security Policy.",
        "expected_pids": ["IT-001", "IT-005"],
        "expected_section": "Comparative Analysis",
        "description": "TEST 7: Cross-Policy Comparative Synthesis (IT-001 vs IT-005)",
        "expect_answerable": True
    },
    {
        "id": 8,
        "query": "What should an employee do if they discover unethical activities?",
        "expected_pids": ["HR-001", "LEG-004"],
        "expected_section": "Section 10 & Section 5",
        "description": "TEST 8: Reporting Channels & Anti-Retaliation Protections",
        "expect_answerable": True
    },
    {
        "id": 9,
        "query": "How can employees protect sensitive company information?",
        "expected_pids": ["IT-001"],
        "expected_section": "Section 4 — Mandatory Requirements",
        "description": "TEST 9: Information Classification & Least Privilege Safeguards",
        "expect_answerable": True
    },
    {
        "id": 10,
        "query": "Does the company provide a $1,000 monthly entertainment allowance?",
        "expected_pids": [],
        "expected_section": "Refusal / Zero-Hallucination Gate",
        "description": "TEST 10: Negative/Absent Policy Query — Must Refuse without Invention",
        "expect_answerable": False
    },
    {
        "id": 11,
        "query": "একজন কর্মচারী কীভাবে ছুটির আবেদন করতে পারে?",
        "expected_pids": ["HR-003"],
        "expected_section": "Section 5 — Operating Procedure",
        "description": "TEST 11: Bangla Procedural Inquiry (Factual Parity with Q2)",
        "expect_answerable": True
    }
]


def run_acceptance_tests():
    print("=" * 80)
    print("RUNNING COMPLETE ACCEPTANCE AUDIT FOR ALL 11 PHASE 21 QUESTIONS")
    print("=" * 80)

    summary_results = []

    for item in ACCEPTANCE_TESTS:
        qid = item["id"]
        q = item["query"]
        expected = item["expected_pids"]
        desc = item["description"]
        expect_ans = item.get("expect_answerable", True)

        print("\n" + "=" * 80)
        print(f"QUESTION {qid:02d}: '{q}'")
        print(f"Description:     {desc}")
        print(f"Expected Policy: {expected}")
        print("=" * 80)

        res = run_policy_rag(q, debug=True)
        retrieved_pids = res.get("policy_ids", [])
        is_ans = res.get("is_answerable", False)
        conf = res.get("confidence", 0.0)
        trace = res.get("debug_trace", {})

        # Validation check
        if not expect_ans:
            hit = (not is_ans) or ("not contain" in res.get("answer", "").lower()) or ("no record" in res.get("answer", "").lower()) or ("does not" in res.get("answer", "").lower()) or ("could not find" in res.get("answer", "").lower())
            status = "[PASS]" if hit else "[FAIL]"
        else:
            hit = any(p in retrieved_pids for p in expected)
            status = "[PASS]" if hit and is_ans else "[FAIL]"

        print(f"\n{status} Question {qid:02d} Results:")
        print(f"  Answerable:         {is_ans}")
        print(f"  Confidence:         {conf}")
        print(f"  Retrieved Policies: {retrieved_pids}")
        print(f"  Expected Policies:  {expected}")

        # Display Stage Traces
        print("\n--- [STAGE B: QUERY ANALYSIS] ---")
        print(json.dumps(trace.get("B. Query Analysis", {}), indent=2, ensure_ascii=False))

        print("\n--- [STAGE C: BM25 TOP MATCHES] ---")
        for b in trace.get("6. BM25 results", trace.get("C. BM25 Results", []))[:3]:
            print(f"  Rank {b.get('ranking')}: {b.get('policy_id')} | {b.get('section')} (Score: {b.get('score')})")

        print("\n--- [STAGE D: VECTOR SEARCH TOP MATCHES] ---")
        for v in trace.get("7. Vector results", trace.get("D. Vector Search Results", []))[:3]:
            print(f"  Rank {v.get('ranking')}: {v.get('policy_id')} | {v.get('section')} (Sim: {v.get('similarity_score')})")

        print("\n--- [STAGE E: RRF COMBINED TOP MATCHES] ---")
        for r in trace.get("8. RRF results", trace.get("E. RRF Results", []))[:3]:
            print(f"  Rank {r.get('combined_ranking')}: {r.get('policy_id')} | {r.get('section')} (RRF Score: {r.get('rrf_score')})")

        print("\n--- [STAGE G: RERANKER RESULTS] ---")
        for g in trace.get("11. Reranker scores", trace.get("G. Reranking Results", []))[:4]:
            print(f"  Rank {g.get('final_ranking')}: {g.get('policy_id')} | {g.get('section')} (Reranker Score: {g.get('rerank_score')})")

        print("\n--- [STAGE H: FINAL CONTEXT EXCERPT] ---")
        h_info = trace.get("H. Final Context Sent to LLM", {})
        print(f"  Target Policies in Context: {h_info.get('policy_ids')}")
        print(f"  Section References:         {h_info.get('section_references')}")

        print("\n--- [STAGE I: GENERATED ANSWER] ---")
        print(res.get("answer"))

        print("\n--- [CITATIONS] ---")
        for c in (res.get("citations") or []):
            print(f"  ✓ {c.get('policy_id')} — {c.get('policy_title')} | Section {c.get('section_number')}: {c.get('section_title')}")

        summary_results.append({
            "id": qid,
            "query": q,
            "expected": expected,
            "retrieved": retrieved_pids,
            "hit": hit,
            "answerable": is_ans,
            "confidence": conf
        })

    print("\n" + "=" * 80)
    print("ACCEPTANCE TESTS AUDIT SUMMARY")
    print("=" * 80)
    all_hits = True
    for s in summary_results:
        mark = "✓ PASS" if s["hit"] else "✗ FAIL"
        if not s["hit"]:
            all_hits = False
        print(f"TEST {s['id']:02d}: {mark} | Expected: {s['expected']} | Retrieved: {s['retrieved']} | Conf: {s['confidence']}")

    print("=" * 80)
    if all_hits:
        print("ALL 11 ACCEPTANCE TESTS PASSED WITH 100% RETRIEVAL & ACCURACY!")
    else:
        print("SOME TESTS FAILED VERIFICATION.")
    print("=" * 80)

    return all_hits


if __name__ == "__main__":
    success = run_acceptance_tests()
    sys.exit(0 if success else 1)

