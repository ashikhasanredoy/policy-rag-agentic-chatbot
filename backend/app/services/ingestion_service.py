import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.loader import document_loader
from backend.app.rag.chunker import PolicyChunker, DocumentChunk
from backend.app.rag.qdrant_store import qdrant_store
from backend.app.rag.bm25 import bm25_index
from backend.app.database.models import Policy, PolicyVersion
from backend.app.database.repository import PolicyRepository

# In-memory document storage cache for BM25 rebuilds
ALL_CHUNKS_REGISTRY: List[Dict[str, Any]] = []

class IngestionService:
    def __init__(self):
        self.chunker = PolicyChunker(chunk_size=300, chunk_overlap=50)

    async def ingest_document(
        self,
        db: AsyncSession,
        file_path: str,
        name: str,
        category: str,
        department: str,
        version: str = "1.0",
        description: str = "",
        status: str = "active",
        effective_date: str = "2026-01-01",
        created_by: str = "System Admin"
    ) -> Policy:
        repo = PolicyRepository(db)

        # 1. Check or create Policy record in DB
        existing_policy = await repo.get_by_name(name)
        if not existing_policy:
            slug = name.lower().replace(" ", "-").replace("/", "-")
            policy = Policy(
                name=name,
                slug=slug,
                category=category,
                department=department,
                description=description or f"{name} document",
                current_version=version,
                status=status
            )
            policy = await repo.create(policy)
        else:
            policy = existing_policy
            await repo.update(policy.id, current_version=version, status=status)

        # 2. Extract text and page breakdown
        full_text, page_texts = document_loader.load_file(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else len(full_text)

        # 3. Add PolicyVersion record in DB
        pol_version = PolicyVersion(
            policy_id=policy.id,
            version=version,
            file_path=file_path,
            file_name=Path(file_path).name,
            file_size=file_size,
            status=status,
            changelog=f"Ingested version {version}",
            created_by=created_by
        )
        await repo.add_version(pol_version)

        # 4. Chunk document
        chunks = self.chunker.chunk_policy_document(
            full_text=full_text,
            policy_id=policy.id,
            policy_name=policy.name,
            category=category,
            department=department,
            version=version,
            status=status,
            effective_date=effective_date,
            page_texts=page_texts
        )

        logger.info(f"Generated {len(chunks)} chunks for policy '{name}' (v{version})")

        # 5. Index into Qdrant
        qdrant_store.upsert_chunks(chunks)

        # 6. Update BM25 Index
        for chunk in chunks:
            ALL_CHUNKS_REGISTRY.append(chunk.to_dict())

        bm25_index.fit(ALL_CHUNKS_REGISTRY)
        logger.info(f"Ingestion complete for '{name}'. Total indexed corpus size: {len(ALL_CHUNKS_REGISTRY)} chunks.")

        return policy

    async def ingest_raw_text(
        self,
        db: AsyncSession,
        name: str,
        category: str,
        department: str,
        content: str,
        version: str = "1.0",
        description: str = "",
        status: str = "active"
    ) -> Policy:
        # Save text to uploads dir
        file_name = f"{name.lower().replace(' ', '_')}_v{version}.txt"
        file_path = os.path.join(settings.UPLOADS_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return await self.ingest_document(
            db=db,
            file_path=file_path,
            name=name,
            category=category,
            department=department,
            version=version,
            description=description,
            status=status
        )

    def rebuild_all_indexes(self):
        """Rebuilds BM25 index from registry."""
        bm25_index.fit(ALL_CHUNKS_REGISTRY)

ingestion_service = IngestionService()
