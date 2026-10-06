from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.exceptions import PolicyRAGException
from backend.app.database.connection import init_db
from backend.app.api.v1.router import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Enterprise Policy RAG System database...")
    await init_db()
    
    # Auto-seed sample policies & default admin if DB is empty
    try:
        from backend.app.database.connection import AsyncSessionLocal
        from scripts.seed_database import seed_initial_data
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)
    except Exception as e:
        logger.warning(f"Auto-seed check: {e}")
        
    yield
    logger.info("Enterprise Policy RAG System shutdown.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise-grade Policy RAG + Agentic AI with strict 'No evidence -> No answer' guardrails.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.exception_handler(PolicyRAGException)
async def policy_rag_exception_handler(request: Request, exc: PolicyRAGException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message, "details": exc.details}
    )

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "api_v1": f"{settings.API_V1_PREFIX}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
