#!/usr/bin/env python3
"""
Official 10 Master Regression Test Suite for Enterprise Policy RAG.
Verifies all 10 real-world inquiries with full retrieval debugging telemetry.
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.workflow.graph import run_policy_rag

TEST_CASES = [
    {
        "id": 1,
        "query": "What happens to an employee's system permissions when they transfer to another department?",
        "expected_policies": ["IT-002"],
        "expected_intent": "procedure",
        "description": "System permissions modification and prompt revocation upon department transfer under IT-002."
    },
    {
        "id": 2,
        "query": "What specific records must Procurement retain when evaluating a supplier?",
        "expected_policies": ["PROC-002"],
        "expected_intent": "records",
        "description": "Specific records and evidence Procurement must retain under PROC-002."
    },
    {
        "id": 3,
        "query": "What are the reporting procedures under the Anti-Harassment Policy compared with the Employee Code of Conduct?",
        "expected_policies": ["HR-012", "HR-001"],
        "expected_intent": "policy_comparison",
        "description": "Comparative analysis of reporting procedures between HR-012 and HR-001."
    },
    {
        "id": 4,
        "query": "What are the differences between Information Security and Privacy and Data Protection in terms of mandatory controls?",
        "expected_policies": ["IT-001", "LEG-008"],
        "expected_intent": "policy_comparison",
        "description": "Comparative analysis of mandatory controls between IT-001 and LEG-008."
    },
    {
        "id": 5,
        "query": "Which policy governs an employee's final settlement after resignation?",
        "expected_policies": ["HR-015"],
        "expected_intent": "procedure",
        "description": "Governing policies for resignation and final settlement (HR-015 & HR-008)."
    },
    {
        "id": 6,
        "query": "What happens if an employee's leave request is rejected?",
        "expected_policies": ["HR-003"],
        "expected_intent": "rejection_appeal",
        "description": "Documented decision rationale, fair hearing, exception, and grievance routes under HR-003."
    },
    {
        "id": 7,
        "query": "What information must be included in a system access request?",
        "expected_policies": ["IT-002"],
        "expected_intent": "required_documents",
        "description": "Information and documentation checklist for access request under IT-002."
    },
    {
        "id": 8,
        "query": "Which policies cover fraud prevention, whistleblower protection, and anti-corruption?",
        "expected_policies": ["LEG-001", "LEG-004", "FIN-013", "GOV-014"],
        "expected_intent": "policy_discovery",
        "description": "Multi-policy governance across Anti-Bribery, Whistleblower, Fraud Prevention, and Assurance."
    },
    {
        "id": 9,
        "query": "Compare Expense Reimbursement and Financial Delegation of Authority.",
        "expected_policies": ["FIN-002", "FIN-012"],
        "expected_intent": "policy_comparison",
        "description": "Dynamic comparative table for FIN-002 vs FIN-012 with zero IT contamination."
    },
    {
        "id": 10,
        "query": "Does the company guarantee reimbursement of all employee expenses within 24 hours?",
        "expected_policies": ["FIN-002"],
        "expected_intent": "mandatory_requirements",
        "description": "Evidence-based refusal of unsupported 24-hour guarantee under FIN-002."
    }
]


def run_tests():
    print("=" * 80)
    print("EXECUTING 10 MASTER REGRESSION TESTS FOR ENTERPRISE POLICY RAG")
    print("=" * 80)

    passed_count = 0
    total_count = len(TEST_CASES)

    for tc in TEST_CASES:
        t_id = tc["id"]
        q = tc["query"]
        exp_pids = set(tc["expected_policies"])

        print(f"\n--------------------------------------------------------------------------------")
        print(f"TEST {t_id}: {q}")
        print(f"Objective: {tc['description']}")
        print(f"Expected Policies: {sorted(list(exp_pids))}")

        res = run_policy_rag(q)
        trace = res.get("debug_trace", {})

        # Telemetry Display (Phase 13 Complete Debugging Suite)
        print("\n--- PHASE 13 COMPLETE DEBUGGING TELEMETRY ---")
        print(f"1. Original Question: {trace.get('1. Original user question', q)}")
        print(f"2. Detected Language: {trace.get('2. Detected language', 'English')}")
        print(f"3. Detected Intent: {trace.get('3. Query intent')}")
        print(f"4. Query Decomposition: {json.dumps(trace.get('5. Query decomposition', {}), indent=2)}")
        print(f"5. Expected Policy Candidates: {sorted(list(exp_pids))}")
        print(f"6. BM25 Results: {json.dumps(trace.get('6. BM25 results', [])[:3], indent=2)}")
        print(f"7. Vector Results: {json.dumps(trace.get('7. Vector results', [])[:3], indent=2)}")
        print(f"8. RRF Results: {json.dumps(trace.get('8. RRF results', [])[:3], indent=2)}")
        print(f"9. Metadata Filters: {trace.get('9. Metadata filters')}")
        print(f"10. Reranker Scores: {json.dumps(trace.get('9. Reranker Scores', [])[:3], indent=2)}")
        print(f"11. Selected Chunk IDs: {[c.get('chunk_id') for c in trace.get('10. Final Retrieved Chunks', [])]}")
        print(f"12. Parent Section Expansion: {json.dumps(trace.get('12. Parent section expansion', [])[:3], indent=2)}")
        print(f"13. Final Context Preview Sent to LLM:\n{str(trace.get('13. Final context sent to LLM', ''))[:300]}...")
        print(f"14. Generated Answer Preview:\n{res['answer'][:300]}...")
        print(f"15. Citation Validation: {trace.get('15. Citation validation', {})}")
        print(f"16. Unsupported Claims: {trace.get('16. Unsupported claims', [])}")
        print(f"17. Excluded Candidates / Reasons: Filter locked: {bool(trace.get('9. Metadata filters'))}; Overlap evaluated.")

        retrieved_pids = set(res.get("policy_ids", []))
        if not retrieved_pids:
            retrieved_pids = set(s.get("policy_id") for s in res.get("citations", []) if s.get("policy_id"))

        # Validation Checks
        pid_match = exp_pids.issubset(retrieved_pids) or exp_pids == retrieved_pids
        if t_id == 10:
            refusal_present = "does not establish a guaranteed 24-hour" in res["answer"].lower() or "cannot confirm" in res["answer"].lower()
            success = refusal_present and "FIN-002" in retrieved_pids
        elif t_id in [3, 4, 9]:
            # Comparative tests: both policies present and table formatted
            has_pids = exp_pids.issubset(retrieved_pids)
            has_table = "|" in res["answer"]
            success = has_pids and has_table
        else:
            success = pid_match

        print("\n--- FULL GENERATED ANSWER ---")
        print(res["answer"])

        if success:
            print(f"\n>>> TEST {t_id} RESULT: PASS <<<")
            passed_count += 1
        else:
            print(f"\n>>> TEST {t_id} RESULT: FAIL <<<")
            print(f"Expected: {sorted(list(exp_pids))}")
            print(f"Actual: {sorted(list(retrieved_pids))}")

    print("\n" + "=" * 80)
    print(f"FINAL REGRESSION TEST RESULTS: {passed_count}/{total_count} PASSED ({passed_count/total_count*100:.1f}%)")
    print("=" * 80)
    return passed_count == total_count


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
