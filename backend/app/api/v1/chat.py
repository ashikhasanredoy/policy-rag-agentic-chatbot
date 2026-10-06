from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.connection import get_db
from backend.app.schemas.chat import ChatRequest, ChatResponse, ConversationResponse, FeedbackRequest
from backend.app.schemas.common import BaseResponse
from backend.app.services.chat_service import chat_service
from backend.app.database.repository import ChatRepository
from backend.app.dependencies import get_current_user_optional
from backend.app.database.models import User, Feedback

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = user.id if user else None
    return await chat_service.process_chat(db=db, request=request, user_id=user_id)

@router.get("/conversations", response_model=BaseResponse[List[ConversationResponse]])
async def list_user_conversations(
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    chat_repo = ChatRepository(db)
    user_id = user.id if user else None
    convs = await chat_repo.get_conversations_by_user(user_id)
    return BaseResponse(
        data=[ConversationResponse.model_validate(c) for c in convs],
        message="Conversations retrieved"
    )

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    chat_repo = ChatRepository(db)
    messages = await chat_repo.get_messages(conversation_id)
    return BaseResponse(
        data=[{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "answerable": m.answerable,
            "confidence": m.confidence,
            "sources": m.sources,
            "latency_ms": m.latency_ms or 0.0,
            "trace": {
                "relevance_passed": (m.retrieval_log.relevance_score >= 0.6) if m.retrieval_log else (len(m.sources or []) > 0),
                "relevance_score": m.retrieval_log.relevance_score if m.retrieval_log else 0.0,
                "answerability_passed": m.answerable,
                "answerability_score": m.retrieval_log.answerability_score if m.retrieval_log else 0.0,
                "faithfulness_passed": (m.retrieval_log.faithfulness_score >= 0.7) if m.retrieval_log else True,
                "faithfulness_score": m.retrieval_log.faithfulness_score if m.retrieval_log else 1.0,
                "conflict_detected": False
            } if m.role == "assistant" else None,
            "created_at": m.created_at
        } for m in messages],
        message="Messages retrieved"
    )

@router.delete("/conversations/{conversation_id}", response_model=BaseResponse[dict])
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    chat_repo = ChatRepository(db)
    user_id = user.id if user else None
    deleted = await chat_repo.delete_conversation(conversation_id, user_id=user_id)
    if not deleted:
        return BaseResponse(
            success=False,
            data={"conversation_id": conversation_id, "deleted": False},
            message="Conversation not found or unauthorized"
        )
    return BaseResponse(
        data={"conversation_id": conversation_id, "deleted": True},
        message="Conversation deleted successfully"
    )

@router.post("/feedback", response_model=BaseResponse[dict])
async def submit_feedback(
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    fb = Feedback(
        message_id=feedback.message_id,
        user_id=user.id if user else None,
        rating=feedback.rating,
        comment=feedback.comment
    )
    db.add(fb)
    await db.commit()
    return BaseResponse(data={"feedback_id": fb.id}, message="Feedback recorded. Thank you!")
