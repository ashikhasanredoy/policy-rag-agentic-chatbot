"""
Okapi BM25 Lexical Retriever for Enterprise Policies.
Prioritizes exact policy IDs, department codes, section titles, and terminology.
"""

import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from src.config.settings import settings
from src.ingestion.chunking import PolicyChunk


class BM25PolicyRetriever:
    """Keyword retriever implementing Okapi BM25 with tokenization tuned for enterprise policies."""

    def __init__(self, top_k: int = settings.BM25_TOP_K):
        self.top_k = top_k
        self.corpus: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    STOPWORDS = {
        "what", "is", "the", "are", "can", "how", "does", "who", "under", "for",
        "in", "to", "into", "like", "their", "an", "a", "or", "and", "of", "on",
        "at", "with", "by", "from", "which", "about", "before", "after", "must",
        "be", "steps", "followed", "should", "if", "they", "do", "get", "all", "any",
        "give", "tell", "explain", "find", "show", "would"
    }

    @staticmethod
    def stem(w: str) -> str:
        """Lightweight Porter/Snowball-style suffix reduction for policy terms."""
        w = w.lower()
        for suff in ["ement", "ing", "ies", "tions", "tion", "ed", "es", "s"]:
            if w.endswith(suff) and len(w) - len(suff) >= 3:
                return w[:-len(suff)]
        return w

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        """
        Tokenization that preserves exact policy IDs (e.g. HR-001, FIN-002),
        filters stopwords, stems English suffixes, and preserves Bengali Unicode tokens.
        """
        if not text:
            return []
        text_lower = text.lower()
        raw_tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*|[\u0980-\u09FF]+", text_lower)
        tokens = []
        for t in raw_tokens:
            if re.search(r"[\u0980-\u09FF]", t):
                tokens.append(t)
                continue
            if "-" in t:
                tokens.append(t)
                for part in t.split("-"):
                    if part and part not in cls.STOPWORDS and len(part) > 1:
                        tokens.append(part)
                continue
            if t in cls.STOPWORDS or len(t) <= 1:
                continue
            tokens.append(t)
            st = cls.stem(t)
            if st != t and len(st) > 2:
                tokens.append(st)
        return tokens

    def index_chunks(self, chunks: List[PolicyChunk]):
        """Builds the BM25 index over candidate policy chunks."""
        self.corpus = [c.to_dict() for c in chunks]
        self.tokenized_corpus = []

        for c in self.corpus:
            # Enrich chunk tokens with explicit policy ID and department terms
            meta = c.get("metadata", {})
            header = f"{meta.get('policy_id', '')} {meta.get('policy_title', '')} {meta.get('department', '')} {meta.get('section_title', '')}"
            combined = f"{header} {c['text']}"
            self.tokenized_corpus.append(self.tokenize(combined))

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _ensure_loaded(self):
        """Auto-loads corpus from Chroma store if uninitialized."""
        if self.bm25 is None or not self.corpus:
            try:
                from src.retrievers.vector_retriever import chroma_retriever
                results = chroma_retriever.collection.get(include=["documents", "metadatas"])
                if results and results.get("ids"):
                    chunks = []
                    for cid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                        chunks.append(PolicyChunk(
                            chunk_id=cid,
                            parent_id=meta.get("parent_id", ""),
                            text=doc,
                            metadata=meta
                        ))
                    self.index_chunks(chunks)
            except Exception as e:
                pass

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Performs BM25 search with optional metadata constraints."""
        self._ensure_loaded()
        if not self.bm25 or not self.corpus:
            return []

        k = top_k or self.top_k
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Pair scores with corpus items and apply filters
        ranked_candidates = []
        for idx, score in enumerate(scores):
            if score <= 0.0:
                continue

            item = self.corpus[idx]
            meta = item.get("metadata", {})

            # Filter check
            if filter_metadata:
                match = True
                for fk, fv in filter_metadata.items():
                    if fv and str(meta.get(fk, "")).lower() != str(fv).lower():
                        match = False
                        break
                if not match:
                    continue

            # Boost exact policy ID match
            query_str = query.upper()
            if meta.get("policy_id") and meta.get("policy_id") in query_str:
                score *= 3.0

            # Boost exact policy title match
            policy_title = str(meta.get("policy_title", "")).lower()
            query_lower = query.lower()
            if policy_title and len(policy_title) > 4 and policy_title in query_lower:
                score *= 3.5
            elif policy_title and len(policy_title.split()) > 1:
                t_words = set(w for w in policy_title.split() if len(w) > 3)
                if t_words and t_words.issubset(set(query_lower.split())):
                    score *= 2.5

            ranked_candidates.append({
                "chunk_id": item["chunk_id"],
                "text": item["text"],
                "score": float(score),
                "metadata": meta,
                "retriever": "bm25"
            })

        # Sort descending by score
        ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
        return ranked_candidates[:k]


bm25_retriever = BM25PolicyRetriever()
