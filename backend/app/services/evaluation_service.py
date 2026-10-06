import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.chat import ChatRequest
from backend.app.services.chat_service import chat_service
from backend.app.core.logging import logger

class EvaluationService:
    async def evaluate_dataset(
        self,
        db: AsyncSession,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs automated benchmark evaluation on a list of test questions.
        Expected test case format:
        {
          "question": "...",
          "answerable": True/False,
          "expected_policy": "..." (optional)
        }
        """
        total = len(test_cases)
        if total == 0:
            return {"total": 0, "metrics": {}}

        answerable_true_positives = 0
        answerable_true_negatives = 0
        false_positives = 0  # Said answerable when it wasn't (Hallucination risk!)
        false_negatives = 0  # Said unanswerable when it was
        policy_hits = 0
        policy_eval_count = 0
        total_latency = 0.0
        details = []

        for idx, tc in enumerate(test_cases):
            q = tc.get("question", "")
            expected_answerable = tc.get("answerable", True)
            expected_policy = tc.get("expected_policy")

            req = ChatRequest(message=q)
            res = await chat_service.process_chat(db=db, request=req)

            total_latency += res.latency_ms
            predicted_answerable = res.answerable

            # Check Answerability
            if expected_answerable and predicted_answerable:
                answerable_true_positives += 1
            elif not expected_answerable and not predicted_answerable:
                answerable_true_negatives += 1
            elif not expected_answerable and predicted_answerable:
                false_positives += 1
            elif expected_answerable and not predicted_answerable:
                false_negatives += 1

            # Check Policy Retrieval Hit
            policy_hit = False
            if expected_policy and expected_answerable:
                policy_eval_count += 1
                retrieved_policies = [s.policy.lower() for s in res.sources]
                if any(expected_policy.lower() in rp for rp in retrieved_policies):
                    policy_hits += 1
                    policy_hit = True

            details.append({
                "question": q,
                "expected_answerable": expected_answerable,
                "predicted_answerable": predicted_answerable,
                "policy_hit": policy_hit if expected_policy else None,
                "latency_ms": res.latency_ms,
                "answer_preview": res.answer[:120]
            })

        no_answer_test_count = sum(1 for tc in test_cases if not tc.get("answerable", True))
        no_answer_accuracy = (
            (answerable_true_negatives / no_answer_test_count) * 100.0
            if no_answer_test_count > 0 else 100.0
        )
        overall_accuracy = ((answerable_true_positives + answerable_true_negatives) / total) * 100.0
        policy_recall = (policy_hits / policy_eval_count * 100.0) if policy_eval_count > 0 else 100.0
        avg_latency = total_latency / total

        return {
            "total_questions": total,
            "overall_answerability_accuracy_pct": round(overall_accuracy, 2),
            "no_answer_accuracy_pct": round(no_answer_accuracy, 2),
            "retrieval_policy_recall_pct": round(policy_recall, 2),
            "false_positive_hallucination_count": false_positives,
            "average_latency_ms": round(avg_latency, 2),
            "details": details
        }

evaluation_service = EvaluationService()
