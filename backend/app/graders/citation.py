from typing import List, Dict, Any
from backend.app.schemas.chat import CitationSource

class CitationExtractor:
    @staticmethod
    def extract_citations(documents: List[Dict[str, Any]]) -> List[CitationSource]:
        """
        Converts retrieved & verified document chunks into structured CitationSource objects.
        Deduplicates by (policy, section, page).
        """
        citations = []
        seen = set()

        for doc in documents:
            meta = doc.get("metadata", {})
            policy_name = meta.get("policy_name", "Company Policy")
            section = meta.get("section", "General")
            page = meta.get("page", 1)
            version = meta.get("version", "1.0")
            score = float(doc.get("rerank_score", doc.get("score", 0.0)))
            text_snippet = doc.get("text", "")[:200] + "..." if len(doc.get("text", "")) > 200 else doc.get("text", "")

            key = (policy_name, section, page, version)
            if key not in seen:
                seen.add(key)
                citations.append(
                    CitationSource(
                        policy=policy_name,
                        section=section,
                        page=page,
                        version=version,
                        score=score,
                        text_snippet=text_snippet
                    )
                )

        return citations

citation_extractor = CitationExtractor()
