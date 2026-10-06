import time
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.chat import ChatRequest, ChatResponse, CitationSource, GraderTrace
from backend.app.database.models import Conversation, Message, RetrievalLog
from backend.app.database.repository import ChatRepository
from backend.app.graph.workflow import policy_rag_agent
from backend.app.core.logging import logger

class ChatService:
    async def process_chat(
        self,
        db: AsyncSession,
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> ChatResponse:
        start_time = time.perf_counter()
        chat_repo = ChatRepository(db)

        # 1. Manage Conversation Session
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = str(uuid.uuid4())
            new_conv = Conversation(
                id=conv_id,
                user_id=user_id,
                title=request.message[:40] + ("..." if len(request.message) > 40 else "")
            )
            await chat_repo.create_conversation(new_conv)
        else:
            existing = await chat_repo.get_conversation(conv_id)
            if not existing:
                new_conv = Conversation(id=conv_id, user_id=user_id, title=request.message[:40])
                await chat_repo.create_conversation(new_conv)

        # 2. Record User Message
        user_msg_id = str(uuid.uuid4())
        await chat_repo.add_message(
            Message(
                id=user_msg_id,
                conversation_id=conv_id,
                role="user",
                content=request.message
            )
        )

        # 3. Prepare Initial Agent State
        initial_state = {
            "query": request.message,
            "department_filter": request.department_filter,
            "category_filter": request.category_filter,
            "intent": "",
            "normalized_keywords": [],
            "search_query": "",
            "retrieved_documents": [],
            "relevant_documents": [],
            "relevance_score": 0.0,
            "relevance_passed": False,
            "answerable": False,
            "answerability_score": 0.0,
            "answerability_reason": "",
            "conflict_detected": False,
            "conflict_details": None,
            "answer": "",
            "confidence": 1.0,
            "citations": [],
            "faithfulness_score": 1.0,
            "faithfulness_passed": True,
            "unsupported_claims": [],
            "retry_count": 0,
            "max_retries": 2,
            "status": "answered",
            "execution_trace": {}
        }

        # 4. Invoke LangGraph Agentic Pipeline
        logger.info(f"Invoking LangGraph Policy Agent for query: '{request.message}'")
        final_state = await policy_rag_agent.ainvoke(initial_state)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 5. Format Output
        answer = final_state.get("answer", "")
        answerable = final_state.get("answerable", False)
        status = final_state.get("status", "answered")
        trace_data = final_state.get("execution_trace", {})

        # Sources
        raw_citations = final_state.get("citations", [])
        sources = [CitationSource(**c) if isinstance(c, dict) else c for c in raw_citations]

        # 6. Record Assistant Message in DB
        asst_msg_id = str(uuid.uuid4())
        await chat_repo.add_message(
            Message(
                id=asst_msg_id,
                conversation_id=conv_id,
                role="assistant",
                content=answer,
                answerable=answerable,
                confidence=final_state.get("confidence", 1.0),
                sources=[s.model_dump() for s in sources],
                latency_ms=latency_ms
            )
        )

        # 7. Record Retrieval & Guardrail Log
        retrieval_log = RetrievalLog(
            message_id=asst_msg_id,
            user_id=user_id,
            query=request.message,
            rewritten_query=final_state.get("search_query"),
            retrieved_chunks_count=len(final_state.get("retrieved_documents", [])),
            reranked_chunks_count=len(final_state.get("relevant_documents", [])),
            relevance_score=final_state.get("relevance_score", 0.0),
            answerability_score=final_state.get("answerability_score", 0.0),
            faithfulness_score=final_state.get("faithfulness_score", 1.0),
            status=status,
            execution_trace=trace_data
        )
        await chat_repo.log_retrieval(retrieval_log)

        # 8. Construct Grader Trace for Frontend UI
        trace = GraderTrace(
            relevance_passed=final_state.get("relevance_passed", False),
            relevance_score=final_state.get("relevance_score", 0.0),
            answerability_passed=answerable,
            answerability_score=final_state.get("answerability_score", 0.0),
            faithfulness_passed=final_state.get("faithfulness_passed", True),
            faithfulness_score=final_state.get("faithfulness_score", 1.0),
            retry_count=final_state.get("retry_count", 0),
            conflict_detected=final_state.get("conflict_detected", False),
            conflict_details=final_state.get("conflict_details")
        )

        return ChatResponse(
            conversation_id=conv_id,
            message_id=asst_msg_id,
            answer=answer,
            answerable=answerable,
            confidence=final_state.get("confidence", 1.0),
            sources=sources,
            trace=trace,
            latency_ms=round(latency_ms, 2)
        )

chat_service = ChatService()
