"""
Ensemble Retriever with Reciprocal Rank Fusion (RRF).
Merges ranked candidate lists from BM25 and Vector similarity search.
"""

from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.retrievers.vector_retriever import chroma_retriever
from src.retrievers.bm25_retriever import bm25_retriever


class RRFEnsembleRetriever:
    """Ensemble retriever combining dense vector and sparse lexical results via RRF."""

    def __init__(
        self,
        rrf_constant: int = settings.RRF_CONSTANT,
        bm25_weight: float = 0.50,
        vector_weight: float = 0.50,
        candidate_pool: int = 40
    ):
        self.rrf_constant = rrf_constant
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.candidate_pool = candidate_pool

    def retrieve(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        vector_top_k: int = settings.VECTOR_TOP_K,
        bm25_top_k: int = settings.BM25_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Runs vector and BM25 retrievers in parallel, fuses their ranks using RRF,
        deduplicates chunks, and returns the top ranked candidates.
        """
        # 1. Retrieve candidates
        vector_results = chroma_retriever.search(
            query=query,
            top_k=vector_top_k,
            filter_metadata=filter_metadata
        )

        bm25_results = bm25_retriever.search(
            query=query,
            top_k=bm25_top_k,
            filter_metadata=filter_metadata
        )

        # 2. Compute RRF Scores
        # Formula: RRF(d) = Σ weight_i / (k + rank_i(d))
        rrf_scores: Dict[str, float] = {}
        candidate_map: Dict[str, Dict[str, Any]] = {}

        # Add vector ranks
        for rank, item in enumerate(vector_results, start=1):
            cid = item["chunk_id"]
            rrf_score = self.vector_weight / (self.rrf_constant + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            if cid not in candidate_map:
                candidate_map[cid] = dict(item)
                candidate_map[cid]["vector_rank"] = rank
            else:
                candidate_map[cid]["vector_rank"] = rank

        # Add BM25 ranks
        for rank, item in enumerate(bm25_results, start=1):
            cid = item["chunk_id"]
            rrf_score = self.bm25_weight / (self.rrf_constant + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            if cid not in candidate_map:
                candidate_map[cid] = dict(item)
                candidate_map[cid]["bm25_rank"] = rank
            else:
                candidate_map[cid]["bm25_rank"] = rank

        # 3. Sort candidates by fused RRF score
        sorted_candidates = []
        for cid, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            entry = candidate_map[cid]
            entry["rrf_score"] = score
            sorted_candidates.append(entry)

        return sorted_candidates[:self.candidate_pool]


ensemble_retriever = RRFEnsembleRetriever()
