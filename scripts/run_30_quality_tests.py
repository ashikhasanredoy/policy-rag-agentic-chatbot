#!/usr/bin/env python3
"""
30-Question Enterprise Benchmark across All 10 Departments.
Evaluates:
- Precision@K (K=3, K=5)
- Recall@K (K=3, K=5)
- MRR (Mean Reciprocal Rank)
- nDCG@5
- Citation Accuracy
- Answer Faithfulness
- Unsupported Claim Rate
- Cross-Policy Contamination Rate
"""

import sys
import math
import time
import json
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.workflow.graph import run_policy_rag
from src.retrievers.multi_query import MultilingualQueryExpander

BENCHMARK_QUESTIONS: List[Dict[str, Any]] = [
    # 1. Exact Policy ID Questions
    {
        "id": "Q01",
        "category": "Exact Policy ID",
        "dept": "Finance",
        "question": "What is FIN-002?",
        "ground_truth_pids": ["FIN-002"],
        "answerable": True
    },
    {
        "id": "Q02",
        "category": "Exact Policy ID",
        "dept": "Human Resources",
        "question": "What are the mandatory requirements of HR-003?",
        "ground_truth_pids": ["HR-003"],
        "answerable": True
    },
    {
        "id": "Q03",
        "category": "Exact Policy ID",
        "dept": "Information Technology",
        "question": "Explain the operating procedure of IT-002.",
        "ground_truth_pids": ["IT-002"],
        "answerable": True
    },
    {
        "id": "Q04",
        "category": "Exact Policy ID",
        "dept": "Legal & Compliance",
        "question": "What is covered under LEG-001?",
        "ground_truth_pids": ["LEG-001"],
        "answerable": True
    },

    # 2. Policy Title Questions
    {
        "id": "Q05",
        "category": "Policy Title",
        "dept": "Finance",
        "question": "What is the procedure for employee expense reimbursement?",
        "ground_truth_pids": ["FIN-002"],
        "answerable": True
    },
    {
        "id": "Q06",
        "category": "Policy Title",
        "dept": "Human Resources",
        "question": "How can an employee apply for leave under the leave management policy?",
        "ground_truth_pids": ["HR-003"],
        "answerable": True
    },
    {
        "id": "Q07",
        "category": "Policy Title",
        "dept": "Information Technology",
        "question": "What are the rules regarding password and authentication?",
        "ground_truth_pids": ["IT-003"],
        "answerable": True
    },
    {
        "id": "Q08",
        "category": "Policy Title",
        "dept": "Operations",
        "question": "What is the operational process for business continuity?",
        "ground_truth_pids": ["OPS-001"],
        "answerable": True
    },
    {
        "id": "Q09",
        "category": "Policy Title",
        "dept": "Corporate Security",
        "question": "What is the procedure for security incident reporting?",
        "ground_truth_pids": ["SEC-002"],
        "answerable": True
    },
    {
        "id": "Q10",
        "category": "Policy Title",
        "dept": "Procurement",
        "question": "How should competitive bidding be conducted in procurement?",
        "ground_truth_pids": ["PROC-003"],
        "answerable": True
    },

    # 3. Semantic / Conceptual Questions
    {
        "id": "Q11",
        "category": "Semantic",
        "dept": "Human Resources",
        "question": "What happens when an employee violates the code of conduct?",
        "ground_truth_pids": ["HR-001"],
        "answerable": True
    },
    {
        "id": "Q12",
        "category": "Semantic",
        "dept": "Information Technology",
        "question": "How does the company grant and revoke system access?",
        "ground_truth_pids": ["IT-002"],
        "answerable": True
    },
    {
        "id": "Q13",
        "category": "Semantic",
        "dept": "Finance",
        "question": "Who can approve financial delegation of authority limits?",
        "ground_truth_pids": ["FIN-012"],
        "answerable": True
    },
    {
        "id": "Q14",
        "category": "Semantic",
        "dept": "Sales",
        "question": "What are the rules regarding customer discount approvals and pricing?",
        "ground_truth_pids": ["SALES-004"],
        "answerable": True
    },
    {
        "id": "Q15",
        "category": "Semantic",
        "dept": "Marketing",
        "question": "What is the approval process for advertising and marketing claims?",
        "ground_truth_pids": ["MKT-002", "MKT-003"],
        "answerable": True
    },
    {
        "id": "Q16",
        "category": "Semantic",
        "dept": "Governance",
        "question": "How does the organization govern AI use and corporate ethics?",
        "ground_truth_pids": ["GOV-009"],
        "answerable": True
    },
    {
        "id": "Q17",
        "category": "Semantic",
        "dept": "Legal & Compliance",
        "question": "What protections are provided to employees reporting violations under whistleblower rules?",
        "ground_truth_pids": ["LEG-004"],
        "answerable": True
    },

    # 4. Bangla Multilingual Questions
    {
        "id": "Q18",
        "category": "Bangla",
        "dept": "Human Resources",
        "question": "একজন কর্মচারী কীভাবে ছুটির আবেদন করতে পারে?",
        "ground_truth_pids": ["HR-003"],
        "answerable": True
    },
    {
        "id": "Q19",
        "category": "Bangla",
        "dept": "Human Resources",
        "question": "কর্মচারী অসদাচরণ করলে কী ধরনের ব্যবস্থা নেওয়া যায়?",
        "ground_truth_pids": ["HR-001", "HR-014"],
        "answerable": True
    },
    {
        "id": "Q20",
        "category": "Bangla",
        "dept": "Finance",
        "question": "ব্যয় প্রতিদানের নিয়ম এবং অনুমোদন পদ্ধতি কী?",
        "ground_truth_pids": ["FIN-002"],
        "answerable": True
    },
    {
        "id": "Q21",
        "category": "Bangla",
        "dept": "Finance",
        "question": "Explain the Finance Department's reimbursement procedure in Bangla.",
        "ground_truth_pids": ["FIN-002"],
        "answerable": True
    },
    {
        "id": "Q22",
        "category": "Bangla",
        "dept": "Corporate Security",
        "question": "কর্মক্ষেত্রে নিরাপত্তা ঘটনা ঘটলে কীভাবে রিপোর্ট করতে হবে?",
        "ground_truth_pids": ["SEC-002"],
        "answerable": True
    },

    # 5. Cross-Policy Comparison Questions
    {
        "id": "Q23",
        "category": "Cross-Policy",
        "dept": "HR & Legal",
        "question": "Compare the employee grievance policy with the whistleblower protection policy.",
        "ground_truth_pids": ["HR-013", "LEG-004"],
        "answerable": True
    },
    {
        "id": "Q24",
        "category": "Cross-Policy",
        "dept": "Finance & Procurement",
        "question": "How do travel expense reimbursement rules relate to general corporate procurement spend approval?",
        "ground_truth_pids": ["FIN-014", "FIN-011", "PROC-004"],
        "answerable": True
    },
    {
        "id": "Q25",
        "category": "Cross-Policy",
        "dept": "IT & Security",
        "question": "What is the relationship between physical access security and information technology endpoint device security?",
        "ground_truth_pids": ["OPS-010", "SEC-001", "IT-004"],
        "answerable": True
    },

    # 6. Specific Section Questions
    {
        "id": "Q26",
        "category": "Specific Section",
        "dept": "Finance",
        "question": "What records and evidence must be retained under FIN-002 Section 7?",
        "ground_truth_pids": ["FIN-002"],
        "answerable": True
    },
    {
        "id": "Q27",
        "category": "Specific Section",
        "dept": "Human Resources",
        "question": "Who are the designated authorities under HR-003 Section 6?",
        "ground_truth_pids": ["HR-003"],
        "answerable": True
    },
    {
        "id": "Q28",
        "category": "Specific Section",
        "dept": "Information Technology",
        "question": "What are the monitoring and assurance requirements in IT-002 Section 8?",
        "ground_truth_pids": ["IT-002"],
        "answerable": True
    },

    # 7. Unanswerable Questions (Safety & Hallucination Resistance)
    {
        "id": "Q29",
        "category": "Unanswerable",
        "dept": "General",
        "question": "Does the company provide a $5,000 cash subsidy for employee private submarine tours?",
        "ground_truth_pids": [],
        "answerable": False
    },
    {
        "id": "Q30",
        "category": "Unanswerable",
        "dept": "General",
        "question": "What is the official procedure for launching orbital spacecraft from headquarters?",
        "ground_truth_pids": [],
        "answerable": False
    }
]


def dcg_at_k(r, k):
    r = r[:k]
    return sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(r))


def ndcg_at_k(r, k):
    dcg = dcg_at_k(r, k)
    ideal = sorted(r, reverse=True)
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0


def run_benchmark():
    print("=" * 80)
    print("STARTING 30-QUESTION ENTERPRISE QUALITY BENCHMARK")
    print("Covering all 10 departments across 7 inquiry categories")
    print("=" * 80)

    results = []

    p_at_3_list = []
    p_at_5_list = []
    r_at_3_list = []
    r_at_5_list = []
    mrr_list = []
    ndcg_list = []
    citation_accuracies = []
    faithfulness_scores = []
    unsupported_count = 0
    contamination_count = 0

    SAFE_REFUSAL_STRING = "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably."

    for idx, test in enumerate(BENCHMARK_QUESTIONS, 1):
        qid = test["id"]
        cat = test["category"]
        dept = test["dept"]
        q = test["question"]
        gt_pids = test["ground_truth_pids"]
        is_answerable = test["answerable"]

        start_t = time.perf_counter()
        rag_res = run_policy_rag(q, debug=True)
        latency = (time.perf_counter() - start_t) * 1000.0

        ans = rag_res["answer"]
        retrieved_pids = rag_res["policy_ids"]
        citations = rag_res["citations"]
        confidence = rag_res["confidence"]

        # 1. Unanswerable Question Check
        if not is_answerable:
            refused_correctly = (
                SAFE_REFUSAL_STRING in ans or
                "no sufficient" in ans.lower() or
                confidence == 0.0 or
                len(retrieved_pids) == 0
            )
            score_p = 1.0 if refused_correctly else 0.0
            p_at_3_list.append(score_p)
            p_at_5_list.append(score_p)
            r_at_3_list.append(score_p)
            r_at_5_list.append(score_p)
            mrr_list.append(score_p)
            ndcg_list.append(score_p)
            citation_accuracies.append(1.0 if len(citations) == 0 else 0.0)
            faithfulness_scores.append(1.0 if refused_correctly else 0.0)

            results.append({
                "id": qid,
                "category": cat,
                "question": q,
                "answerable": False,
                "status": "PASS" if refused_correctly else "FAIL",
                "retrieved": retrieved_pids,
                "latency_ms": round(latency, 1)
            })
            print(f"[{qid}] {cat} ({dept}): '{q[:50]}...' -> Refusal verified ({'PASS' if refused_correctly else 'FAIL'})")
            continue

        # 2. Information Retrieval Metrics
        k3 = retrieved_pids[:3]
        k5 = retrieved_pids[:5]

        # Precision@K
        hits_3 = [p for p in k3 if p in gt_pids]
        p3 = len(hits_3) / len(k3) if k3 else 0.0
        p_at_3_list.append(p3)

        hits_5 = [p for p in k5 if p in gt_pids]
        p5 = len(hits_5) / len(k5) if k5 else 0.0
        p_at_5_list.append(p5)

        # Recall@K
        r3 = len(set(hits_3)) / len(gt_pids) if gt_pids else 0.0
        r_at_3_list.append(min(1.0, r3))

        r5 = len(set(hits_5)) / len(gt_pids) if gt_pids else 0.0
        r_at_5_list.append(min(1.0, r5))

        # MRR
        rr = 0.0
        for rank, p in enumerate(retrieved_pids, 1):
            if p in gt_pids:
                rr = 1.0 / rank
                break
        mrr_list.append(rr)

        # nDCG@5
        rel_scores = [1.0 if p in gt_pids else 0.0 for p in k5]
        ndcg_list.append(ndcg_at_k(rel_scores, 5))

        # Citation Accuracy
        if citations:
            cite_pids = [c.get("policy_id") for c in citations]
            valid_cites = [cp for cp in cite_pids if cp in gt_pids]
            cite_acc = len(valid_cites) / len(citations)
        else:
            cite_acc = 1.0 if any(p in ans for p in gt_pids) else 0.0
        citation_accuracies.append(cite_acc)

        # Faithfulness & Contamination Checks
        ans_lower = ans.lower()
        has_concur = "concur" in ans_lower and "no mention of concur" not in ans_lower
        has_500 = ("$500" in ans_lower or "500 usd" in ans_lower) and "no $500 limit" not in ans_lower

        if has_concur or has_500:
            unsupported_count += 1
            faithfulness = 0.0
        else:
            faithfulness = 1.0
        faithfulness_scores.append(faithfulness)

        # Cross-policy contamination (for single policy questions)
        if len(gt_pids) == 1:
            foreign_pids = [p for p in retrieved_pids if p != gt_pids[0]]
            if foreign_pids:
                contamination_count += 1

        status = "PASS" if (rr > 0 and faithfulness == 1.0) else "FAIL"
        results.append({
            "id": qid,
            "category": cat,
            "question": q,
            "ground_truth": gt_pids,
            "retrieved": retrieved_pids,
            "precision@3": round(p3, 2),
            "recall@3": round(r3, 2),
            "mrr": round(rr, 2),
            "latency_ms": round(latency, 1),
            "status": status
        })

        print(f"[{qid}] {cat} ({dept}): '{q[:50]}...' -> Retrieved: {retrieved_pids} (MRR: {rr:.2f}, Status: {status})")

    # Aggregate Metrics
    avg_p3 = sum(p_at_3_list) / len(p_at_3_list)
    avg_p5 = sum(p_at_5_list) / len(p_at_5_list)
    avg_r3 = sum(r_at_3_list) / len(r_at_3_list)
    avg_r5 = sum(r_at_5_list) / len(r_at_5_list)
    avg_mrr = sum(mrr_list) / len(mrr_list)
    avg_ndcg = sum(ndcg_list) / len(ndcg_list)
    avg_cite_acc = sum(citation_accuracies) / len(citation_accuracies)
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
    unsupported_rate = unsupported_count / len(BENCHMARK_QUESTIONS)
    contamination_rate = contamination_count / len([q for q in BENCHMARK_QUESTIONS if len(q["ground_truth_pids"]) == 1])

    summary = {
        "total_test_questions": len(BENCHMARK_QUESTIONS),
        "precision_at_3": round(avg_p3, 4),
        "precision_at_5": round(avg_p5, 4),
        "recall_at_3": round(avg_r3, 4),
        "recall_at_5": round(avg_r5, 4),
        "mrr": round(avg_mrr, 4),
        "ndcg_at_5": round(avg_ndcg, 4),
        "citation_accuracy": round(avg_cite_acc, 4),
        "answer_faithfulness": round(avg_faithfulness, 4),
        "unsupported_claim_rate": round(unsupported_rate, 4),
        "cross_policy_contamination_rate": round(contamination_rate, 4)
    }

    print("\n" + "=" * 80)
    print("30-QUESTION BENCHMARK EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Test Inquiries:             {summary['total_test_questions']}")
    print(f"Precision@3:                      {summary['precision_at_3'] * 100:.1f}%")
    print(f"Precision@5:                      {summary['precision_at_5'] * 100:.1f}%")
    print(f"Recall@3:                         {summary['recall_at_3'] * 100:.1f}%")
    print(f"Recall@5:                         {summary['recall_at_5'] * 100:.1f}%")
    print(f"Mean Reciprocal Rank (MRR):       {summary['mrr']:.4f}")
    print(f"nDCG@5:                           {summary['ndcg_at_5']:.4f}")
    print(f"Citation Accuracy:                {summary['citation_accuracy'] * 100:.1f}%")
    print(f"Answer Faithfulness:              {summary['answer_faithfulness'] * 100:.1f}%")
    print(f"Unsupported Claim Rate:           {summary['unsupported_claim_rate'] * 100:.1f}%")
    print(f"Cross-Policy Contamination Rate:  {summary['cross_policy_contamination_rate'] * 100:.1f}%")
    print("=" * 80)

    benchmark_output_path = PROJECT_ROOT / "docs" / "BENCHMARK_RESULTS_30.json"
    with open(benchmark_output_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "details": results}, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed evaluation results written to: {benchmark_output_path}")


if __name__ == "__main__":
    run_benchmark()

