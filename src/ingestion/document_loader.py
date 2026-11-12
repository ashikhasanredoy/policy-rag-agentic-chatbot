"""
Unified Document Loader for Enterprise Policy Documents.
Prioritizes DOCX for structured extraction; falls back to PDF on error.
Prevents duplicate indexing of DOCX and PDF copies.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.ingestion.docx_loader import DocxPolicyLoader
from src.ingestion.pdf_loader import PdfPolicyLoader
from src.ingestion.markdown_parser import markdown_parser
from src.ingestion.metadata_extractor import metadata_registry


class UnifiedPolicyLoader:
    """Loads and normalizes an enterprise policy document with fallback."""

    @staticmethod
    def load_policy(file_path: Path) -> Dict[str, Any]:
        """Loads a policy document, preferring Markdown > DOCX > PDF."""
        ext = file_path.suffix.lower()

        # If given a PDF or DOCX but a sibling MD exists, prefer MD
        if ext in [".pdf", ".docx"]:
            md_sibling = file_path.with_suffix(".md")
            if md_sibling.exists():
                file_path = md_sibling
                ext = ".md"

        result: Optional[Dict[str, Any]] = None

        if ext in [".md", ".markdown"]:
            result = markdown_parser.parse(file_path)
        elif ext == ".docx":
            try:
                result = DocxPolicyLoader.load(file_path)
            except Exception as e:
                # Fallback to sibling PDF if DOCX parsing fails
                pdf_sibling = file_path.with_suffix(".pdf")
                if pdf_sibling.exists():
                    result = PdfPolicyLoader.load(pdf_sibling)
                    result["metadata"]["fallback_used"] = True
                else:
                    raise e
        elif ext == ".pdf":
            result = PdfPolicyLoader.load(file_path)
        else:
            raise ValueError(f"Unsupported policy document format: {ext}")

        # Enrich and validate metadata using master Policy Register
        result["metadata"] = metadata_registry.enrich(result["metadata"])

        return result


unified_loader = UnifiedPolicyLoader()

