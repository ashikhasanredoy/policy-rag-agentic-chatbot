"""
Configuration module for Enterprise Policy RAG system.
Loads settings from environment variables and provides sensible production defaults.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Project Paths
    PROJECT_NAME: str = "Enterprise Policy RAG System"
    PROJECT_ROOT: Path = PROJECT_ROOT
    POLICIES_DIR: Path = PROJECT_ROOT / "policies"
    ORIGINAL_DOCS_DIR: Path = PROJECT_ROOT / "original_documents"
    METADATA_DIR: Path = PROJECT_ROOT / "metadata"
    REGISTER_CSV: Path = PROJECT_ROOT / "metadata" / "Policy_Register.csv"
    PROCESSED_DATA_DIR: Path = PROJECT_ROOT / "processed"
    CHROMA_PERSIST_DIR: Path = PROJECT_ROOT / "vectorstore" / "chroma_db"
    CACHE_DIR: Path = PROJECT_ROOT / "processed" / "cache"

    # Vector DB
    VECTOR_DB_TYPE: str = "chroma"  # "chroma" or "qdrant"
    CHROMA_COLLECTION_NAME: str = "enterprise_policies"
    QDRANT_URL: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "enterprise_policies"

    # Embedding & Reranker Models
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    EMBEDDING_DIMENSION: int = 1024
    USE_MOCK_MODELS: bool = True  # Fast, reproducible local embedding & reranking without hanging on 2.3GB network downloads

    # Retrieval Parameters
    BM25_TOP_K: int = 20
    VECTOR_TOP_K: int = 20
    RRF_CONSTANT: int = 60
    BM25_WEIGHT: float = 0.40
    VECTOR_WEIGHT: float = 0.60
    CANDIDATE_POOL: int = 20
    FINAL_RERANKED_CHUNKS: int = 6
    FINAL_TOP_K: int = 5

    # Chunking Configuration
    TARGET_CHUNK_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 60
    PRESERVE_COMPLETE_SECTIONS: bool = True

    # Multi-Query Expansion
    ENABLE_MULTI_QUERY: bool = True
    NUM_EXPANDED_QUERIES: int = 3

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # "openai", "gemini", "anthropic", "ollama", "mock"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Server Configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Ensure necessary directories exist
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
