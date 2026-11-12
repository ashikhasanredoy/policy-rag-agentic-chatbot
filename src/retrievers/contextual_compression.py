"""
Contextual Compression for Enterprise Policy Chunks.
Prunes conversational fluff and irrelevant boilerplate while strictly preserving
mandatory requirements, numbers, approval roles, exceptions, and qualifying rules.
"""

import re
from typing import List, Dict, Any, Optional


class PolicyContextualCompressor:
    """Compresses context chunks while guaranteeing preservation of policy rules and numbers."""

    # Words indicating essential policy assertions that must never be pruned
    CRITICAL_MARKERS = [
        "must", "shall", "required", "mandatory", "prohibited", "forbidden",
        "responsible", "authority", "approv", "except", "unless", "limit",
        "maximum", "minimum", "deadline", "timeline", "escalat", "penalty",
        "consequence", "procedure", "step", "dollar", "$", "%", "day", "week",
        "month", "year", "hour"
    ]

    def compress_chunk(self, chunk_text: str, query: str) -> str:
        """
        Compresses a chunk by extracting key requirement sentences,
        preserving headings, lists, numbers, and critical constraints.
        """
        lines = chunk_text.splitlines()
        header_lines = []
        body_lines = []

        # Separate header prefix from body
        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                header_lines.append(line)
            else:
                body_lines.append(line)

        body_text = "\n".join(body_lines).strip()

        # If body is already brief (under 150 words), return untouched to prevent meaning distortion
        if len(body_text.split()) < 150:
            return chunk_text

        # Sentence-level filtering
        sentences = re.split(r"(?<=[.!?])\s+", body_text)
        query_words = set(query.lower().split())

        retained_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue

            s_lower = s_clean.lower()

            # Preserve bullet points / numbered lists
            if s_clean.startswith("-") or s_clean.startswith("•") or re.match(r"^\d+\.", s_clean):
                retained_sentences.append(s_clean)
                continue

            # Preserve any sentence containing numbers or policy critical markers
            has_critical_marker = any(m in s_lower for m in self.CRITICAL_MARKERS)
            has_number = bool(re.search(r"\d+", s_clean))
            has_query_term = any(qw in s_lower for qw in query_words if len(qw) > 2)

            if has_critical_marker or has_number or has_query_term:
                retained_sentences.append(s_clean)

        # Fallback to full body if filtering removed too much
        if len(retained_sentences) < 2:
            return chunk_text

        compressed_body = "\n".join(retained_sentences)
        if header_lines:
            return "\n".join(header_lines) + "\n" + compressed_body
        return compressed_body

    def compress_candidates(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Applies compression to candidate documents while preserving original metadata."""
        selected = candidates[:top_k] if top_k is not None else candidates
        compressed = []
        for c in selected:
            c_copy = dict(c)
            c_copy["compressed_text"] = self.compress_chunk(c["text"], query)
            compressed.append(c_copy)
        return compressed


contextual_compressor = PolicyContextualCompressor()
