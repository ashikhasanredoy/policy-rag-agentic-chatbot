"""
DOCX Loader for Enterprise Policy documents.
Extracts structured sections, headings, bullets, and table metadata.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import docx
from docx.document import Document as _DocumentClass


class DocxPolicyLoader:
    """Parses standard enterprise policy DOCX files into structured sections and metadata."""

    @staticmethod
    def load(file_path: Path) -> Dict[str, Any]:
        doc: _DocumentClass = docx.Document(str(file_path))

        metadata: Dict[str, Any] = {
            "source_file": str(file_path),
            "file_type": "DOCX",
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

        # 1. Parse Metadata from Tables
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                for i in range(0, len(cells) - 1, 2):
                    label = cells[i].lower().replace(":", "").strip()
                    val = cells[i + 1].strip() if i + 1 < len(cells) else ""
                    if not val:
                        continue
                    if "policy id" in label:
                        metadata["policy_id"] = val
                    elif "document owner" in label or "owner" in label:
                        metadata["owner"] = val
                    elif "approval authority" in label or "approved by" in label:
                        metadata["approver"] = val
                    elif "version" in label:
                        metadata["version"] = val
                    elif "effective date" in label:
                        metadata["effective_date"] = val.replace(" (placeholder)", "")
                    elif "next review" in label or "review date" in label:
                        metadata["review_date"] = val.replace(" (placeholder)", "")
                    elif "classification" in label:
                        metadata["classification"] = val
                    elif "status" in label:
                        metadata["status"] = val

        # 2. Parse Paragraphs (Title, Department Code, Headings, Bullets, Text)
        sections: List[Dict[str, Any]] = []
        current_section = {
            "section_number": "0",
            "section_title": "Document Information",
            "content": []
        }

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style = p.style.name if p.style else ""

            # Check title
            if style == "Title" and not metadata["policy_title"]:
                metadata["policy_title"] = text
                continue

            # Check department info line (e.g. "Human Resources  •  Version 1.0")
            if "•" in text and not metadata["department"]:
                dept_candidate = text.split("•")[0].strip()
                if dept_candidate:
                    metadata["department"] = dept_candidate

            # Detect numbered headings (e.g. "1. Purpose", "Heading 1")
            heading_match = re.match(r"^(\d+)\.\s+(.+)$", text)
            if heading_match or style.startswith("Heading"):
                # Save previous section if it has content
                if current_section["content"]:
                    sections.append({
                        "section_number": current_section["section_number"],
                        "section_title": current_section["section_title"],
                        "text": "\n".join(current_section["content"]).strip()
                    })

                if heading_match:
                    sec_num = heading_match.group(1)
                    sec_title = heading_match.group(2).strip()
                else:
                    sec_num = str(len(sections) + 1)
                    sec_title = text

                current_section = {
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "content": []
                }
            else:
                # Format bullets cleanly
                if style in ("List Bullet", "List Paragraph") or text.startswith("•") or text.startswith("-"):
                    cleaned = re.sub(r"^[•\-]\s*", "", text)
                    current_section["content"].append(f"- {cleaned}")
                else:
                    current_section["content"].append(text)

        # Append last section
        if current_section["content"]:
            sections.append({
                "section_number": current_section["section_number"],
                "section_title": current_section["section_title"],
                "text": "\n".join(current_section["content"]).strip()
            })

        # Infer department code from policy_id or path
        if metadata["policy_id"]:
            metadata["department_code"] = metadata["policy_id"].split("-")[0]
        else:
            code_match = re.search(r"([A-Z]{2,5})-\d{3}", file_path.name)
            if code_match:
                metadata["policy_id"] = code_match.group(0)
                metadata["department_code"] = code_match.group(1)

        return {
            "metadata": metadata,
            "sections": sections,
            "full_text": "\n\n".join(f"## {s['section_number']}. {s['section_title']}\n{s['text']}" for s in sections)
        }

