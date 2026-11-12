"""
Dynamic Markdown Policy Parser for Enterprise Policies.
Dynamically detects headings (#, ##, ###), preserves actual section numbers,
titles, numbered procedures, bullet lists, tables, and nested subsections without
assuming fixed section counts or hardcoded section schemas.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.ingestion.metadata_extractor import metadata_registry


class MarkdownPolicyParser:
    """Parses markdown policy documents dynamically, preserving all structural hierarchy."""

    @staticmethod
    def parse(file_path: Path) -> Dict[str, Any]:
        """
        Parses a markdown policy file dynamically.
        Detects frontmatter metadata, arbitrary headings, subsections, lists, and tables.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Policy file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()

        # 1. Extract Document Metadata
        metadata: Dict[str, Any] = {
            "source_file": str(file_path.name),
            "file_path": str(file_path),
            "file_type": "MD"
        }

        # Check for title (# Document Title)
        for line in lines:
            line_s = line.strip()
            if line_s.startswith("# ") and not line_s.startswith("## "):
                metadata["raw_title"] = line_s[2:].strip()
                break

        # Check for key-value frontmatter lines (e.g. **Document ID:** FIN-002)
        kv_pattern = re.compile(r"^\*\*(.+?):\*\*\s*(.*)$")
        body_start_idx = 0
        for i, line in enumerate(lines):
            line_s = line.strip()
            m = kv_pattern.match(line_s)
            if m:
                key = m.group(1).lower().replace(" ", "_")
                val = m.group(2).strip()
                metadata[key] = val
                body_start_idx = i + 1
            elif line_s.startswith("---") and i > 0:
                body_start_idx = i + 1
                break

        # Ensure canonical metadata extraction
        policy_id = metadata.get("document_id") or metadata.get("policy_id")
        if not policy_id:
            # Fallback to filename pattern (e.g. FIN-002_Expense_Reimbursement.md)
            m_id = re.match(r"^([A-Z]{2,5}-\d{3})", file_path.stem)
            if m_id:
                policy_id = m_id.group(1)
        if policy_id:
            metadata["policy_id"] = policy_id

        # Enrich with Policy_Register.csv canonical registry
        if policy_id and policy_id in metadata_registry.registry:
            metadata = metadata_registry.enrich(metadata)
        else:
            # Infer canonical fields from raw frontmatter if not in registry
            if "raw_title" in metadata and "policy_title" not in metadata:
                metadata["policy_title"] = metadata["raw_title"]

        # 2. Parse Dynamic Sections (## headings)
        sections: List[Dict[str, Any]] = []
        current_sec: Optional[Dict[str, Any]] = None
        current_sec_lines: List[str] = []

        # Heading regex: ## [optional number] [title]
        # Supports:
        # ## 1. Purpose
        # ## Section 1: Purpose
        # ## Purpose
        # ## 10. Social Media and External Communication
        # ## 13. Disciplinary Actions
        h2_pattern = re.compile(r"^##\s+(?:(?:Section\s+)?(\d+[A-Za-z]?|[IVXLCDM]+)[\.:\-\s]+)?(.*)$", re.IGNORECASE)
        h3_pattern = re.compile(r"^###\s+(?:(?:Section\s+)?(\d+(?:\.\d+)*|[A-Za-z])[\.:\-\s]+)?(.*)$", re.IGNORECASE)

        body_lines = lines[body_start_idx:]
        sec_index = 1

        for line in body_lines:
            line_s = line.strip()
            if line_s.startswith("## ") and not line_s.startswith("### "):
                # Save previous section
                if current_sec:
                    current_sec["text"] = "\n".join(current_sec_lines).strip()
                    sections.append(current_sec)
                    current_sec_lines = []

                m = h2_pattern.match(line_s)
                if m:
                    sec_num = m.group(1) or str(sec_index)
                    sec_title = m.group(2).strip()
                    if not sec_title and m.group(1):
                        sec_title = m.group(1).strip()
                        sec_num = str(sec_index)
                else:
                    sec_num = str(sec_index)
                    sec_title = line_s[3:].strip()

                current_sec = {
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "heading_raw": line_s,
                    "subsections": []
                }
                sec_index += 1
            elif line_s.startswith("### ") and current_sec:
                # Nested subsection
                m_sub = h3_pattern.match(line_s)
                sub_num = m_sub.group(1) if m_sub and m_sub.group(1) else ""
                sub_title = m_sub.group(2).strip() if m_sub else line_s[4:].strip()
                current_sec["subsections"].append({
                    "sub_number": sub_num,
                    "sub_title": sub_title,
                    "heading_raw": line_s
                })
                current_sec_lines.append(line)
            else:
                if current_sec:
                    current_sec_lines.append(line)
                elif line_s:
                    # Content before first ## heading (e.g. document overview)
                    if not current_sec:
                        current_sec = {
                            "section_number": "0",
                            "section_title": "Overview",
                            "heading_raw": "## Overview",
                            "subsections": []
                        }
                    current_sec_lines.append(line)

        # Flush final section
        if current_sec:
            current_sec["text"] = "\n".join(current_sec_lines).strip()
            sections.append(current_sec)

        metadata["section_count"] = len(sections)

        return {
            "metadata": metadata,
            "sections": sections,
            "full_text": content
        }


markdown_parser = MarkdownPolicyParser()
