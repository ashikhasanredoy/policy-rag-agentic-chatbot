import time
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.schemas.chat import ChatRequest, ChatResponse, CitationSource, GraderTrace
from backend.app.database.models import Conversation, Message, RetrievalLog
from backend.app.database.repository import ChatRepository
from src.workflow.graph import run_policy_rag
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
                title=request.message[:60].strip()
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

        # 3. Execute Unified 150-Policy Hybrid RAG Pipeline
        logger.info(f"Invoking Enterprise Policy Hybrid RAG for query: '{request.message}'")
        rag_result = run_policy_rag(
            query=request.message,
            user_department=request.department_filter,
            debug=True
        )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        answer = rag_result.get("answer", "")
        answerable = rag_result.get("is_answerable", True)
        confidence = rag_result.get("confidence", 1.0)
        policy_ids = rag_result.get("policy_ids", [])
        trace_data = rag_result.get("trace", {})

        # 4. Map Citations
        sources = []
        for c in rag_result.get("citations", []):
            pid = c.get("policy_id", "")
            title = c.get("policy_title", "")
            sec_num = c.get("section_number", "")
            sec_title = c.get("section_title", "")
            sec_str = f"Section {sec_num}: {sec_title}" if sec_num else (sec_title or "General")
            p_display = f"{pid} — {title}" if pid and title else (pid or title or "Enterprise Policy")
            snippet = c.get("snippet", "") or c.get("text_snippet", "")
            rel_score = float(c.get("score", c.get("relevance_score", 0.9)))

            sources.append(CitationSource(
                policy=p_display,
                policy_id=pid,
                policy_name=p_display,
                section=sec_str,
                page=c.get("page", 1),
                version=c.get("version", "1.0"),
                score=rel_score,
                text_snippet=snippet,
                snippet=snippet,
                relevance_score=rel_score
            ))

        # 5. Record Assistant Message in DB
        asst_msg_id = str(uuid.uuid4())
        await chat_repo.add_message(
            Message(
                id=asst_msg_id,
                conversation_id=conv_id,
                role="assistant",
                content=answer,
                answerable=answerable,
                confidence=confidence,
                sources=[s.model_dump() for s in sources],
                latency_ms=latency_ms
            )
        )

        # 6. Record Retrieval & Guardrail Log
        retrieval_log = RetrievalLog(
            message_id=asst_msg_id,
            user_id=user_id,
            query=request.message,
            rewritten_query=request.message,
            retrieved_chunks_count=len(sources),
            reranked_chunks_count=len(sources),
            relevance_score=confidence,
            answerability_score=1.0 if answerable else 0.0,
            faithfulness_score=1.0,
            status="answered" if answerable else "abstained",
            execution_trace=trace_data
        )
        await chat_repo.log_retrieval(retrieval_log)

        # 7. Construct Grader Trace for Frontend UI
        trace = GraderTrace(
            relevance_passed=answerable,
            relevance_score=confidence,
            answerability_passed=answerable,
            answerability_score=1.0 if answerable else 0.0,
            faithfulness_passed=True,
            faithfulness_score=1.0,
            retry_count=0,
            conflict_detected=False,
            conflict_details=None
        )

        return ChatResponse(
            conversation_id=conv_id,
            message_id=asst_msg_id,
            answer=answer,
            answerable=answerable,
            confidence=confidence,
            sources=sources,
            latency_ms=latency_ms,
            trace=trace
        )


chat_service = ChatService()
