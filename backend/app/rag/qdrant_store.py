from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.chunker import DocumentChunk

class QdrantStore:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.client = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        if settings.USE_IN_MEMORY_QDRANT or not settings.QDRANT_URL:
            logger.info("Initializing in-memory Qdrant instance")
            return QdrantClient(location=":memory:")
        else:
            logger.info(f"Connecting to Qdrant cluster at {settings.QDRANT_URL}")
            return QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                dim = embedding_service.dimension
                logger.info(f"Creating Qdrant collection '{self.collection_name}' (dim={dim})")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=dim,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def upsert_chunks(self, chunks: List[DocumentChunk]):
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = embedding_service.embed_documents(texts)

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            point_id = abs(hash(chunk.metadata.chunk_id)) % (2**63 - 1)
            payload = chunk.metadata.to_payload()
            payload["text"] = chunk.text

            points.append(
                qmodels.PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} vectors into Qdrant collection '{self.collection_name}'")

    def search(
        self,
        query: str,
        top_k: int = 10,
        category: Optional[str] = None,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        query_vector = embedding_service.embed_query(query)
        must_conditions = []

        if status:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="status",
                    match=qmodels.MatchValue(value=status)
                )
            )
        if category:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="category",
                    match=qmodels.MatchValue(value=category)
                )
            )
        if department:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="department",
                    match=qmodels.MatchValue(value=department)
                )
            )

        query_filter = qmodels.Filter(must=must_conditions) if must_conditions else None

        results = []
        # Support both new qdrant_client query_points and legacy search API
        if hasattr(self.client, "query_points"):
            res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=top_k
            )
            points = getattr(res, "points", res)
            for r in points:
                results.append({
                    "text": r.payload.get("text", "") if hasattr(r, "payload") else "",
                    "score": float(r.score) if hasattr(r, "score") else 0.0,
                    "metadata": {k: v for k, v in r.payload.items() if k != "text"} if hasattr(r, "payload") else {}
                })
        elif hasattr(self.client, "search"):
            res = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=top_k
            )
            for r in res:
                results.append({
                    "text": r.payload.get("text", ""),
                    "score": float(r.score),
                    "metadata": {k: v for k, v in r.payload.items() if k != "text"}
                })

        return results

    def delete_by_policy_id(self, policy_id: int):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="policy_id",
                                match=qmodels.MatchValue(value=policy_id)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            logger.error(f"Error deleting policy vectors: {e}")

qdrant_store = QdrantStore()
