"""
Retrieval Metrics Calculation Engine for Information Retrieval Evaluation.
Calculates Precision@K, Recall@K, MRR, nDCG@K, and Hit Rate@K against ground-truth policy IDs.
"""

import math
from typing import List, Set, Dict, Any


class RetrievalMetrics:
    """Computes standard IR metrics comparing retrieved candidate items to relevant ground-truth items."""

    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if k <= 0 or not retrieved:
            return 0.0
        top_k = retrieved[:k]
        hits = sum(1 for item in top_k if item in relevant)
        return hits / k

    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if not relevant:
            return 1.0 if not retrieved else 0.0
        top_k = retrieved[:k]
        hits = sum(1 for item in top_k if item in relevant)
        return hits / len(relevant)

    @staticmethod
    def reciprocal_rank(retrieved: List[str], relevant: Set[str]) -> float:
        if not relevant:
            return 1.0 if not retrieved else 0.0
        for rank, item in enumerate(retrieved, start=1):
            if item in relevant:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if not relevant:
            return 1.0 if not retrieved else 0.0
        top_k = retrieved[:k]

        # DCG calculation
        dcg = 0.0
        for i, item in enumerate(top_k, start=1):
            rel = 1.0 if item in relevant else 0.0
            dcg += rel / math.log2(i + 1)

        # Ideal DCG calculation
        ideal_len = min(k, len(relevant))
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_len + 1))

        if idcg <= 0.0:
            return 0.0
        return dcg / idcg

    @staticmethod
    def hit_rate_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if not relevant:
            return 1.0 if not retrieved else 0.0
        top_k = retrieved[:k]
        return 1.0 if any(item in relevant for item in top_k) else 0.0

    @classmethod
    def evaluate_query(
        cls,
        retrieved_ids: List[str],
        relevant_ids: List[str],
        k: int = 5
    ) -> Dict[str, float]:
        rel_set = set(relevant_ids)
        if not rel_set:
            # For unanswerable questions, hit rate is 1.0 if no false positive retrieved
            is_empty = len(retrieved_ids) == 0
            return {
                "precision": 1.0 if is_empty else 0.0,
                "recall": 1.0 if is_empty else 0.0,
                "mrr": 1.0 if is_empty else 0.0,
                "ndcg": 1.0 if is_empty else 0.0,
                "hit_rate": 1.0 if is_empty else 0.0
            }

        return {
            "precision": cls.precision_at_k(retrieved_ids, rel_set, k),
            "recall": cls.recall_at_k(retrieved_ids, rel_set, k),
            "mrr": cls.reciprocal_rank(retrieved_ids, rel_set),
            "ndcg": cls.ndcg_at_k(retrieved_ids, rel_set, k),
            "hit_rate": cls.hit_rate_at_k(retrieved_ids, rel_set, k)
        }

