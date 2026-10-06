from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger

class RelevanceGrader:
    def __init__(self, threshold: float = settings.RELEVANCE_THRESHOLD):
        self.threshold = threshold

    def grade(self, query: str, document: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Evaluates if a document chunk is relevant to the query.
        Returns: (is_relevant, score, reasoning)
        """
        score = float(document.get("rerank_score", document.get("score", 0.0)))
        is_relevant = score >= self.threshold
        reason = f"Relevance score {score:.2f} {'meets' if is_relevant else 'below'} threshold {self.threshold:.2f}"
        return is_relevant, score, reason

    def filter_relevant(self, query: str, documents: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float]:
        relevant_docs = []
        scores = []
        for doc in documents:
            is_rel, sc, _ = self.grade(query, doc)
            if is_rel:
                relevant_docs.append(doc)
                scores.append(sc)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        return relevant_docs, avg_score

relevance_grader = RelevanceGrader()
