import os
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.database.connection import get_db
from backend.app.database.repository import ChatRepository
from backend.app.schemas.common import BaseResponse
from backend.app.services.ingestion_service import ingestion_service
from backend.app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/admin", tags=["Admin Operations"])

@router.post("/policies/upload", response_model=BaseResponse[dict])
async def upload_and_index_policy(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    department: str = Form(...),
    version: str = Form("1.0"),
    description: Optional[str] = Form(""),
    effective_date: Optional[str] = Form("2026-01-01"),
    db: AsyncSession = Depends(get_db)
):
    file_path = os.path.join(settings.UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    policy = await ingestion_service.ingest_document(
        db=db,
        file_path=file_path,
        name=name,
        category=category,
        department=department,
        version=version,
        description=description or "",
        status="active",
        effective_date=effective_date or "2026-01-01",
        created_by="Administrator"
    )

    return BaseResponse(
        data={"policy_id": policy.id, "name": policy.name, "version": version, "status": "indexed"},
        message="Policy document uploaded and multi-index ingestion completed."
    )

@router.post("/rebuild-index", response_model=BaseResponse[dict])
async def rebuild_indexes():
    ingestion_service.rebuild_all_indexes()
    return BaseResponse(data={"status": "Indexes synchronized"}, message="BM25 and Qdrant index synchronization complete")

@router.get("/analytics", response_model=BaseResponse[dict])
async def get_system_analytics(db: AsyncSession = Depends(get_db)):
    chat_repo = ChatRepository(db)
    logs = await chat_repo.get_recent_logs(limit=100)

    total_queries = len(logs)
    answered_queries = sum(1 for l in logs if l.status == "answered")
    abstained_queries = sum(1 for l in logs if "abstained" in l.status)
    conflicts = sum(1 for l in logs if l.status == "conflict_detected")

    avg_relevance = sum(l.relevance_score for l in logs) / total_queries if total_queries > 0 else 0.0
    avg_answerability = sum(l.answerability_score for l in logs) / total_queries if total_queries > 0 else 0.0

    return BaseResponse(
        data={
            "total_queries": total_queries,
            "answered_queries": answered_queries,
            "abstained_queries": abstained_queries,
            "policy_conflicts_flagged": conflicts,
            "average_relevance_score": round(avg_relevance, 3),
            "average_answerability_score": round(avg_answerability, 3),
            "recent_audit_logs": [{
                "id": l.id,
                "query": l.query,
                "status": l.status,
                "retrieved": l.retrieved_chunks_count,
                "created_at": l.created_at
            } for l in logs[:15]]
        },
        message="Analytics retrieved"
    )

@router.post("/evaluate", response_model=BaseResponse[dict])
async def trigger_rag_evaluation(db: AsyncSession = Depends(get_db)):
    import json
    questions_file = os.path.join(settings.BASE_DIR, "data", "evaluation", "questions.json")
    if os.path.exists(questions_file):
        with open(questions_file, "r") as f:
            test_cases = json.load(f)
    else:
        test_cases = [
            {"question": "How many days of annual leave do employees get per year?", "answerable": True, "expected_policy": "Annual Leave"},
            {"question": "What is the maximum daily meal allowance for business travel?", "answerable": True, "expected_policy": "Travel"},
            {"question": "Does the company provide housing allowance or rent stipend?", "answerable": False}
        ]

    eval_result = await evaluation_service.evaluate_dataset(db, test_cases)
    return BaseResponse(data=eval_result, message="RAG benchmark evaluation completed")
