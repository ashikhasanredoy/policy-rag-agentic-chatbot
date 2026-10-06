import os
from typing import List, Dict, Any, Tuple
from pathlib import Path
from backend.app.core.logging import logger
from backend.app.rag.cleaner import clean_text

class DocumentLoader:
    @staticmethod
    def load_pdf(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extracts full text and page-level text breakdown from a PDF.
        Returns (full_text, [{"page_number": int, "text": str}])
        """
        page_texts = []
        full_text_parts = []

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = clean_text(page.get_text())
                if page_text:
                    page_texts.append({
                        "page_number": page_idx + 1,
                        "text": page_text
                    })
                    full_text_parts.append(page_text)
            doc.close()
        except ImportError:
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    page_text = clean_text(page.extract_text() or "")
                    if page_text:
                        page_texts.append({
                            "page_number": idx + 1,
                            "text": page_text
                        })
                        full_text_parts.append(page_text)
            except Exception as e:
                logger.error(f"Failed to read PDF with pypdf: {e}")
        except Exception as e:
            logger.error(f"Failed to read PDF with PyMuPDF: {e}")

        full_text = "\n\n".join(full_text_parts)
        return full_text, page_texts

    @staticmethod
    def load_text_or_markdown(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = clean_text(f.read())
        return content, [{"page_number": 1, "text": content}]

    @classmethod
    def load_file(cls, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == ".pdf":
            return cls.load_pdf(file_path)
        elif ext in [".md", ".markdown", ".txt", ".json"]:
            return cls.load_text_or_markdown(file_path)
        else:
            return cls.load_text_or_markdown(file_path)

document_loader = DocumentLoader()
