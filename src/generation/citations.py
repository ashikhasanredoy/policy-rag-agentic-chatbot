"""
Citation Engine for Enterprise Policy RAG.
Maps retrieved context chunks to structured and user-facing citations.
"""

from typing import List, Dict, Any


class CitationMapper:
    """Builds clean structured citations from candidate chunks."""

    @staticmethod
    def build_citations(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        citations = []
        seen = set()

        for c in candidates:
            meta = c.get("metadata", {})
            pid = meta.get("policy_id", "")
            sec_num = meta.get("section_number", "")
            key = f"{pid}-S{sec_num}"

            if key in seen:
                continue
            seen.add(key)

            snippet = c.get("text", "")
            # Remove chunk prefix line if present
            if snippet.startswith("[") and "]" in snippet:
                snippet = snippet.split("]\n", 1)[-1].strip()

            snippet_preview = snippet[:200] + ("..." if len(snippet) > 200 else "")

            citations.append({
                "policy_id": pid,
                "policy_title": meta.get("policy_title", ""),
                "department": meta.get("department", ""),
                "section_number": sec_num,
                "section_title": meta.get("section_title", ""),
                "version": meta.get("version", "1.0"),
                "source_file": meta.get("source_file", ""),
                "file_type": meta.get("file_type", "DOCX"),
                "score": round(float(c.get("rerank_score", c.get("score", 0.0))), 4),
                "relevance_score": round(float(c.get("rerank_score", c.get("score", 0.0))), 4),
                "snippet": snippet_preview
            })

        return citations


    @classmethod
    def create_citations(cls, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return cls.build_citations(candidates)

    @staticmethod
    def format_citations_markdown(citations: List[Dict[str, Any]]) -> str:
        lines = []
        for idx, c in enumerate(citations, start=1):
            pid = c.get("policy_id", "")
            title = c.get("policy_title", "")
            sec_num = c.get("section_number", "")
            sec_title = c.get("section_title", "")
            sec_str = f"Section {sec_num}: {sec_title}" if sec_num else sec_title
            lines.append(f"[{idx}] **{pid}: {title}** — {sec_str}")
        return "\n".join(lines)


citation_mapper = CitationMapper()
