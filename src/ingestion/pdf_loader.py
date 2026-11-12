"""
PDF Fallback Loader for Enterprise Policy documents.
Extracts structured sections and metadata when DOCX is unavailable.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
import fitz


class PdfPolicyLoader:
    """Fallback PDF parser using PyMuPDF (fitz) for structured section extraction."""

    @staticmethod
    def load(file_path: Path) -> Dict[str, Any]:
        doc = fitz.open(str(file_path))
        raw_lines: List[str] = []

        for page in doc:
            page_text = page.get_text()
            for line in page_text.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if "SYNTHETIC ENTERPRISE POLICY BASELINE" in stripped:
                    continue
                if re.match(r"^Page \d+$", stripped):
                    continue
                raw_lines.append(stripped)
        doc.close()

        metadata: Dict[str, Any] = {
            "source_file": str(file_path),
            "file_type": "PDF",
            "policy_id": "",
            "policy_title": "",
            "department": "",
            "department_code": "",
            "version": "1.0",
            "effective_date": "",
            "review_date": "",
            "classification": "Internal — Template",
            "status": "Draft baseline",
            "owner": "",
            "approver": ""
        }

        # Try to infer ID from filename
        id_match = re.search(r"([A-Z]{2,5})-\d{3}", file_path.name)
        if id_match:
            metadata["policy_id"] = id_match.group(0)
            metadata["department_code"] = id_match.group(1)

        # Parse sections based on "N. Section Name"
        sections: List[Dict[str, Any]] = []
        current_section = {
            "section_number": "0",
            "section_title": "Header Information",
            "content": []
        }

        for line in raw_lines:
            heading_match = re.match(r"^(\d+)\.\s+(.+)$", line)
            if heading_match:
                if current_section["content"]:
                    sections.append({
                        "section_number": current_section["section_number"],
                        "section_title": current_section["section_title"],
                        "text": "\n".join(current_section["content"]).strip()
                    })
                current_section = {
                    "section_number": heading_match.group(1),
                    "section_title": heading_match.group(2).strip(),
                    "content": []
                }
            else:
                if line.startswith("•") or line.startswith("-"):
                    cleaned = re.sub(r"^[•\-]\s*", "", line)
                    current_section["content"].append(f"- {cleaned}")
                else:
                    current_section["content"].append(line)

        if current_section["content"]:
            sections.append({
                "section_number": current_section["section_number"],
                "section_title": current_section["section_title"],
                "text": "\n".join(current_section["content"]).strip()
            })

        return {
            "metadata": metadata,
            "sections": sections,
            "full_text": "\n\n".join(f"## {s['section_number']}. {s['section_title']}\n{s['text']}" for s in sections)
        }

