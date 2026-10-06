import re
from typing import List, Dict, Any
from backend.app.core.config import settings

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what", "which",
    "this", "that", "these", "those", "then", "just", "so", "than", "such",
    "both", "through", "about", "for", "is", "of", "while", "during", "to",
    "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "do", "does", "get", "under", "per", "requires", "under"
}

def stem(w: str) -> str:
    w = w.lower()
    for s in ["ingly", "edly", "fully", "ing", "ly", "ed", "es", "s"]:
        if w.endswith(s) and len(w) > len(s) + 2:
            return w[:-len(s)]
    return w

class CrossEncoderReranker:
    def __init__(self, model_name: str = settings.RERANKER_MODEL_NAME, use_mock: bool = settings.USE_MOCK_MODELS):
        self.model_name = model_name
        self.use_mock = use_mock
        self.model = None

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
        if not documents:
            return []

        for doc in documents:
            doc["rerank_score"] = self._heuristic_score(query, doc.get("text", ""), doc.get("metadata", {}))

        sorted_docs = sorted(documents, key=lambda x: x.get("rerank_score", 0.0), reverse=True)
        return sorted_docs[:top_k]

    def _heuristic_score(self, query: str, text: str, metadata: dict) -> float:
        raw_q = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
        q_tokens = [w for w in raw_q if w not in STOPWORDS]
        if not q_tokens:
            q_tokens = raw_q

        q_stems = set(stem(w) for w in q_tokens)

        raw_t = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
        t_stems = set(stem(w) for w in raw_t)

        sec_words = set(stem(w) for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", metadata.get("section", "").lower()))
        title_words = set(stem(w) for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", metadata.get("policy_name", "").lower()))

        if not q_stems:
            return 0.0

        matches = q_stems.intersection(t_stems)
        overlap = len(matches) / len(q_stems)

        sec_matches = q_stems.intersection(sec_words)
        sec_overlap = len(sec_matches) / len(q_stems)

        title_matches = q_stems.intersection(title_words)
        title_overlap = len(title_matches) / len(q_stems)

        score = (0.45 * overlap) + (0.30 * sec_overlap) + (0.25 * title_overlap)

        if overlap >= 0.25 or sec_overlap >= 0.25:
            score = max(score, overlap, sec_overlap)

        return float(min(1.0, score))

reranker = CrossEncoderReranker()
