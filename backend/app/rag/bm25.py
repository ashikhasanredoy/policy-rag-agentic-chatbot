import math
import re
from collections import Counter
from typing import List, Dict, Any, Tuple

class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths = []
        self.doc_payloads = []  # List of dicts: {"text": ..., "metadata": ...}
        self.doc_freqs = {}     # term -> number of docs containing term
        self.inverted_index = {} # term -> list of (doc_idx, term_freq)

    def tokenize(self, text: str) -> List[str]:
        # Lowercase and extract alphanumeric tokens
        tokens = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
        return tokens

    def fit(self, documents: List[Dict[str, Any]]):
        """Fit BM25 on a list of document dicts with keys 'text' and 'metadata'."""
        self.doc_payloads = documents
        self.corpus_size = len(documents)
        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        total_len = 0
        self.doc_lengths = []
        self.doc_freqs = {}
        self.inverted_index = {}

        for idx, doc in enumerate(documents):
            tokens = self.tokenize(doc.get("text", ""))
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            counts = Counter(tokens)
            for term, freq in counts.items():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
                if term not in self.inverted_index:
                    self.inverted_index[term] = []
                self.inverted_index[term].append((idx, freq))

        self.avg_doc_len = total_len / self.corpus_size if self.corpus_size > 0 else 0.0

    def search(self, query: str, top_k: int = 10, filter_status: str = "active") -> List[Tuple[Dict[str, Any], float]]:
        if self.corpus_size == 0:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = [0.0] * self.corpus_size

        for term in tokens:
            if term not in self.inverted_index:
                continue

            df = self.doc_freqs[term]
            # IDF calculation with standard BM25 smoothing
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

            for doc_idx, tf in self.inverted_index[term]:
                doc_len = self.doc_lengths[doc_idx]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                term_score = idf * ((tf * (self.k1 + 1.0)) / denom)
                scores[doc_idx] += term_score

        # Pair scores with docs and filter
        scored_results = []
        for idx, score in enumerate(scores):
            if score > 0:
                doc = self.doc_payloads[idx]
                meta = doc.get("metadata", {})
                if filter_status and meta.get("status") != filter_status:
                    continue
                scored_results.append((doc, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]

bm25_index = BM25Index()
