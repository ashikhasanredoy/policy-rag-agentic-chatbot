import json
import os
import asyncio
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.connection import AsyncSessionLocal, init_db
from backend.app.services.evaluation_service import evaluation_service
from scripts.seed_database import seed_initial_data

async def run_evaluation():
    logger.info("Initializing DB and loading benchmark questions...")
    await init_db()
    async with AsyncSessionLocal() as session:
        # Ensure data is indexed
        await seed_initial_data(session)

        questions_file = os.path.join(settings.BASE_DIR, "data", "evaluation", "questions.json")
        with open(questions_file, "r") as f:
            test_cases = json.load(f)

        logger.info(f"Running evaluation on {len(test_cases)} benchmark test cases...")
        results = await evaluation_service.evaluate_dataset(session, test_cases)

        print("\n" + "=" * 65)
        print("📊 POLICY RAG & AGENTIC AI BENCHMARK RESULTS")
        print("=" * 65)
        print(f"Total Test Cases:                    {results['total_questions']}")
        print(f"Overall Answerability Accuracy:      {results['overall_answerability_accuracy_pct']}%")
        print(f"No-Answer (Abstention) Precision:   {results['no_answer_accuracy_pct']}%  [CRITICAL]")
        print(f"Retrieval Policy Recall@K:          {results['retrieval_policy_recall_pct']}%")
        print(f"False Positives (Hallucinations):    {results['false_positive_hallucination_count']}")
        print(f"Average Latency:                     {results['average_latency_ms']} ms")
        print("=" * 65)
        print("\nBreakdown of Evaluated Questions:")
        for idx, d in enumerate(results["details"], 1):
            status_icon = "✅" if d["expected_answerable"] == d["predicted_answerable"] else "❌"
            exp_str = "Answerable" if d["expected_answerable"] else "NO-ANSWER"
            pred_str = "Answerable" if d["predicted_answerable"] else "ABSTAINED"
            print(f"{status_icon} [{idx:02d}] Expected: {exp_str:10} | Predicted: {pred_str:10} | Q: {d['question']}")

        print("=" * 65 + "\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
