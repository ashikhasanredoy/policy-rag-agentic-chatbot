"""
Multilingual Cross-Encoder Reranker using BAAI/bge-reranker-v2-m3.
Computes cross-attention relevance scores for (query, document) pairs.
"""

from typing import List, Dict, Any, Optional
from src.config.settings import settings


class CrossEncoderReranker:
    """Reranks candidate documents using cross-encoder architecture."""

    def __init__(
        self,
        model_name: str = settings.RERANKER_MODEL_NAME,
        use_mock: bool = settings.USE_MOCK_MODELS,
        final_top_k: int = settings.FINAL_RERANKED_CHUNKS
    ):
        self.model_name = model_name
        self.use_mock = use_mock
        self.final_top_k = final_top_k
        self._model = None

    def _get_model(self):
        if self._model is None and not self.use_mock:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                # If downloading fails (e.g. offline/no GPU), fall back to fast lexical-semantic scoring
                print(f"⚠️ Notice: Cross-encoder {self.model_name} deferred ({e}). Using lexical-semantic scoring.")
                self.use_mock = True
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        expanded_queries: Optional[List[str]] = None,
        intent: Optional[str] = None,
        target_sections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Scores and re-orders candidate documents based on cross-encoder and intent-driven section relevance."""
        if not candidates:
            return []

        k = top_k or self.final_top_k

        # If only 1 candidate, return it
        if len(candidates) <= 1:
            return candidates[:k]

        from src.retrievers.query_decomposer import query_decomposer
        eff_intent = intent or query_decomposer.classify_intent(query)
        target_secs = target_sections or query_decomposer.get_target_sections_for_intent(eff_intent)

        model = self._get_model()

        if not self.use_mock and model is not None:
            pairs = [[query, c["text"]] for c in candidates]
            scores = model.predict(pairs)
            for idx, s in enumerate(scores):
                c = candidates[idx]
                c_meta = c.get("metadata", {})
                sec_num = str(c_meta.get("section_number", ""))
                sec_boost = 1.5 if (target_secs and sec_num == target_secs[0]) else (1.2 if target_secs and sec_num in target_secs[1:] else 1.0)
                c["rerank_score"] = float(s) * sec_boost
        else:
            # Fallback heuristic: fused RRF + keyword overlap + exact policy ID boost + intent-driven section boost
            import re
            q_words = set(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*|[\u0980-\u09FF]+", query.lower()))
            if expanded_queries:
                for eq in expanded_queries:
                    q_words.update(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*|[\u0980-\u09FF]+", eq.lower()))

            q_upper = query.upper()
            for c in candidates:
                base_score = c.get("rrf_score", c.get("score", 0.5))
                c_text = c.get("text", "").lower()
                c_meta = c.get("metadata", {})

                # Keyword overlap across query & expanded variants
                overlap = sum(1 for w in q_words if w in c_text and len(w) > 2) / max(1, len(q_words))

                # Boost exact policy ID match
                is_exact_id = bool(c_meta.get("policy_id") and c_meta.get("policy_id") in q_upper)
                id_boost = 3.0 if is_exact_id else 1.0
                if is_exact_id:
                    base_score = max(base_score, 0.35)

                # Boost exact policy title match
                pol_title = str(c_meta.get("policy_title", "")).lower()
                title_boost = 2.5 if (pol_title and len(pol_title) > 3 and pol_title in query.lower()) else 1.0
                if pol_title and len(pol_title) > 3 and pol_title in query.lower():
                    base_score = max(base_score, 0.30)

                # Section priority based on query intent (No longer defaulting to Sections 4 and 5)
                sec_num = str(c_meta.get("section_number", ""))
                if target_secs and sec_num == target_secs[0]:
                    sec_boost = 3.5  # Primary target section boost (e.g. Sec 7 for documents, Sec 6 for approver, Sec 10 for discipline)
                elif target_secs and len(target_secs) > 1 and sec_num in target_secs[1:]:
                    sec_boost = 2.0  # Secondary target section boost
                else:
                    sec_boost = 1.0

                # Section title keyword boost
                sec_title = str(c_meta.get("section_title", "")).lower()
                sec_title_words = set(re.findall(r"\w+", sec_title))
                if any(w in q_words for w in sec_title_words if len(w) > 3):
                    sec_boost *= 1.4

                c["rerank_score"] = float(base_score * 0.3 + overlap * 0.7) * id_boost * title_boost * sec_boost

        # Sort descending by rerank_score
        reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)

        # Policy diversity preservation for cross-policy / comparative / discovery queries
        is_multi_intent = (
            eff_intent in ["policy_comparison", "policy_discovery"]
            or any(term in query.lower() for term in [
                "compare", "versus", "vs", "difference", "all policies", "find all", "list all",
                "policies related", "which policies", "what policies", "policies govern",
                "policies address", "policies covering", "policies that cover", "multiple policies"
            ])
        )
        if is_multi_intent:
            diverse = []
            seen_pid_counts = {}
            k_multi = max(k, 12)
            for c in reranked:
                pid = c.get("metadata", {}).get("policy_id")
                seen_pid_counts[pid] = seen_pid_counts.get(pid, 0) + 1
                if seen_pid_counts[pid] <= 2:
                    diverse.append(c)
                if len(diverse) >= k_multi:
                    break
            return diverse

        return reranked[:k]


from typing import Optional
cross_encoder_reranker = CrossEncoderReranker()
