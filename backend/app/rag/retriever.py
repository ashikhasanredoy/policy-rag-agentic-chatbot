from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.rag.qdrant_store import qdrant_store
from backend.app.rag.bm25 import bm25_index
from backend.app.rag.rrf import reciprocal_rank_fusion
from backend.app.rag.reranker import reranker

class HybridRetriever:
    def __init__(
        self,
        retrieval_top_k: int = settings.RETRIEVAL_TOP_K,
        rerank_top_k: int = settings.RERANK_TOP_K
    ):
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_k = rerank_top_k

    def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        department: Optional[str] = None,
        status: str = "active"
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Dense vector search via Qdrant
        2. Sparse lexical search via BM25
        3. Reciprocal Rank Fusion (RRF)
        4. Cross-encoder reranking
        """
        logger.info(f"Hybrid retrieval initiated for query: '{query}' (status={status})")

        # 1. Qdrant Dense Retrieval
        try:
            dense_results = qdrant_store.search(
                query=query,
                top_k=self.retrieval_top_k,
                category=category,
                department=department,
                status=status
            )
        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
            dense_results = []

        # 2. BM25 Sparse Retrieval
        try:
            bm25_raw = bm25_index.search(
                query=query,
                top_k=self.retrieval_top_k,
                filter_status=status
            )
            sparse_results = []
            for doc, score in bm25_raw:
                sparse_results.append({
                    "text": doc.get("text", ""),
                    "score": float(score),
                    "metadata": doc.get("metadata", {})
                })
        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}")
            sparse_results = []

        # If both lists are empty, return empty list
        if not dense_results and not sparse_results:
            logger.warning("No documents retrieved from either dense or sparse indexes.")
            return []

        # 3. Reciprocal Rank Fusion (RRF)
        fused_docs = reciprocal_rank_fusion(
            ranked_lists=[dense_results, sparse_results],
            k=60,
            top_n=max(self.retrieval_top_k, 10)
        )

        # 4. Cross-Encoder Reranking
        reranked_docs = reranker.rerank(
            query=query,
            documents=fused_docs,
            top_k=self.rerank_top_k
        )

        logger.info(f"Retrieved {len(reranked_docs)} candidate chunks after reranking.")
        return reranked_docs

retriever = HybridRetriever()
