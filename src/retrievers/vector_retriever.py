"""
Chroma Vector Retriever with Persistent Local Storage.
Modular design allows switching between Chroma and Qdrant.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from src.config.settings import settings
from src.embeddings.embedding_model import embedding_service
from src.ingestion.chunking import PolicyChunk


class ChromaPolicyRetriever:
    """Manages persistent Chroma vector storage and similarity retrieval."""

    def __init__(
        self,
        persist_dir: Path = settings.CHROMA_PERSIST_DIR,
        collection_name: str = settings.CHROMA_COLLECTION_NAME
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[PolicyChunk], batch_size: int = 100):
        """Indexes policy chunks with embeddings and metadata in batches."""
        if not chunks:
            return

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids = [c.chunk_id for c in batch]
            texts = [c.text for c in batch]
            metadatas = [c.metadata for c in batch]
            embeddings = embedding_service.embed_documents(texts)

            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

    def search(
        self,
        query: str,
        top_k: int = settings.VECTOR_TOP_K,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Performs vector similarity search with optional metadata filtering."""
        query_embedding = embedding_service.embed_query(query)

        # Build Chroma-compatible where filter
        where_filter = None
        if filter_metadata:
            conditions = []
            for k, v in filter_metadata.items():
                if v:
                    conditions.append({k: {"$eq": v}})
            if len(conditions) == 1:
                where_filter = conditions[0]
            elif len(conditions) > 1:
                where_filter = {"$and": conditions}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, self.collection.count())),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        candidates = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

            for doc_id, text, meta, dist in zip(ids, docs, metas, dists):
                # Cosine distance to similarity: 1 - distance
                sim = max(0.0, 1.0 - float(dist)) if dist is not None else 0.0
                candidates.append({
                    "chunk_id": doc_id,
                    "text": text,
                    "score": sim,
                    "metadata": meta,
                    "retriever": "vector"
                })

        return candidates

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )


chroma_retriever = ChromaPolicyRetriever()

