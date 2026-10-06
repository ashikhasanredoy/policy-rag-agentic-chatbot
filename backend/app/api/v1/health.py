from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.rag.qdrant_store import qdrant_store
from backend.app.rag.bm25 import bm25_index

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "olmo_model": settings.OLMO_MODEL_NAME
    }

@router.get("/qdrant")
async def qdrant_health():
    try:
        collections = qdrant_store.client.get_collections().collections
        return {"status": "connected", "collections": [c.name for c in collections]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/bm25")
async def bm25_health():
    return {
        "status": "ready",
        "indexed_documents_count": bm25_index.corpus_size,
        "unique_terms_count": len(bm25_index.doc_freqs)
    }
