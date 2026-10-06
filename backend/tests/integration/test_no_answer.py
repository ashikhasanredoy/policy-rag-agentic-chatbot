import pytest
import pytest_asyncio
from backend.app.database.connection import init_db, AsyncSessionLocal
from backend.app.schemas.chat import ChatRequest
from backend.app.services.chat_service import chat_service
from scripts.seed_database import seed_initial_data

@pytest.mark.asyncio
async def test_no_answer_abstention_pipeline():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

        # 1. Ask a question NOT in any policy (Housing Allowance)
        unanswerable_query = "Does the company provide free personal housing allowance or pet boarding?"
        req = ChatRequest(message=unanswerable_query)
        response = await chat_service.process_chat(session, req)

        assert response.answerable is False
        assert response.confidence == 0.0
        assert len(response.sources) == 0
        assert "couldn't find information" in response.answer or "not available" in response.answer or "not generate" in response.answer

@pytest.mark.asyncio
async def test_valid_policy_answer_with_citations():
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

        # 2. Ask a legitimate policy question
        valid_query = "How many days of paid annual leave do full-time permanent employees get each year?"
        req = ChatRequest(message=valid_query)
        response = await chat_service.process_chat(session, req)

        assert response.answerable is True
        assert len(response.sources) > 0
        assert "20" in response.answer
        assert "Annual Leave" in response.sources[0].policy
