import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# ROOT_DIR points to the project root: /.../policy rag chatbot
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    BASE_DIR: Path = ROOT_DIR
    BACKEND_DIR: Path = BACKEND_DIR
    APP_ENV: str = "development"
    APP_NAME: str = "Enterprise Policy RAG System"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "corporate-super-secret-policy-guardrail-jwt-key-2026-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./policy_rag.db"

    # Qdrant
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "company_policies"
    USE_IN_MEMORY_QDRANT: bool = True

    # Models
    LLM_PROVIDER: str = "olmo"
    OLMO_MODEL_NAME: str = "allenai/OLMo-7B-Instruct"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-base"
    USE_MOCK_MODELS: bool = True

    # RAG & Grader Thresholds calibrated for production long-form policy chunks
    RETRIEVAL_TOP_K: int = 10
    RERANK_TOP_K: int = 4
    RELEVANCE_THRESHOLD: float = 0.35
    ANSWERABILITY_THRESHOLD: float = 0.45
    FAITHFULNESS_THRESHOLD: float = 0.70
    MAX_AGENT_RETRIES: int = 2

    # Storage
    STORAGE_DIR: str = str(BACKEND_DIR / "storage")
    UPLOADS_DIR: str = str(BACKEND_DIR / "storage" / "uploads")

settings = Settings()

os.makedirs(settings.STORAGE_DIR, exist_ok=True)
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
