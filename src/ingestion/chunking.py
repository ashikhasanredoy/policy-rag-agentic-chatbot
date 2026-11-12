"""
Parent-Child Section-Based Chunking Engine for Enterprise Policies.
Produces parent sections for comprehensive context lookup and child chunks
(300-500 tokens) for high-precision vector and BM25 retrieval.
"""

import re
import hashlib
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from src.config.settings import settings


@dataclass
class PolicyChunk:
    chunk_id: str
    parent_id: str
    text: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "parent_id": self.parent_id,
            "text": self.text,
            "metadata": self.metadata
        }


class ParentChildSectionChunker:
    """Chunks structured policy documents preserving section headings and parent-child hierarchy."""

    def __init__(
        self,
        target_tokens: int = settings.TARGET_CHUNK_TOKENS,
        overlap_tokens: int = settings.CHUNK_OVERLAP_TOKENS,
        preserve_complete_sections: bool = settings.PRESERVE_COMPLETE_SECTIONS
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.preserve_complete_sections = preserve_complete_sections

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Fast approximate token count (roughly 1 token ≈ 4 characters or 0.75 words)."""
        words = text.split()
        return max(1, int(len(words) * 1.3))

    def chunk_policy(self, parsed_policy: Dict[str, Any]) -> Tuple[List[PolicyChunk], Dict[str, str]]:
        """
        Takes a parsed document and returns:
        1. List of child PolicyChunk objects for embedding & BM25 indexing.
        2. Dictionary of parent_id -> parent_section_text for parent document retrieval.
        """
        metadata = parsed_policy["metadata"]
        policy_id = metadata.get("policy_id", "POL-UNKNOWN")
        policy_title = metadata.get("policy_title", "Enterprise Policy")
        department = metadata.get("department", "General")
        dept_code = metadata.get("department_code", policy_id.split("-")[0] if "-" in policy_id else "GEN")

        sections = parsed_policy.get("sections", [])
        child_chunks: List[PolicyChunk] = []
        parent_store: Dict[str, str] = {}

        chunk_counter = 1

        for sec in sections:
            sec_num = str(sec.get("section_number", "0"))
            sec_title = sec.get("section_title", "General")
            sec_text = sec.get("text", "").strip()

            if not sec_text:
                continue

            # Standardized Parent ID (e.g. FIN-002-SECTION-05)
            sec_num_clean = re.sub(r"[^0-9a-zA-Z]", "", sec_num)
            if sec_num_clean.isdigit():
                sec_str = sec_num_clean.zfill(2)
            else:
                sec_str = sec_num_clean or "00"

            parent_id = f"{policy_id}-SECTION-{sec_str}"
            full_parent_text = f"## {sec_num}. {sec_title}\n\n{sec_text}"
            parent_store[parent_id] = full_parent_text

            sec_tokens = self.estimate_tokens(sec_text)
            sec_chunk_counter = 1

            # Rule: If complete section fits comfortably within target (or preserve_complete_sections is True), keep intact
            if self.preserve_complete_sections and sec_tokens <= (self.target_tokens * 1.25):
                chunk_id = f"{parent_id}-CHUNK-{str(sec_chunk_counter).zfill(3)}"
                header_prefix = f"[{policy_id}: {policy_title} | Department: {department} | Section {sec_num}: {sec_title}]\n"
                chunk_text = header_prefix + sec_text

                chunk_meta = self._build_metadata(
                    metadata=metadata,
                    sec_num=sec_num,
                    sec_title=sec_title,
                    parent_id=parent_id,
                    chunk_id=chunk_id
                )
                child_chunks.append(PolicyChunk(chunk_id, parent_id, chunk_text, chunk_meta))
                chunk_counter += 1
            else:
                # Subdivide section by paragraphs/bullet boundaries preserving units
                sub_chunks = self._split_section_into_chunks(sec_text, sec_num, sec_title, policy_id, policy_title, department)
                for sub_text in sub_chunks:
                    chunk_id = f"{parent_id}-CHUNK-{str(sec_chunk_counter).zfill(3)}"
                    chunk_meta = self._build_metadata(
                        metadata=metadata,
                        sec_num=sec_num,
                        sec_title=sec_title,
                        parent_id=parent_id,
                        chunk_id=chunk_id
                    )
                    child_chunks.append(PolicyChunk(chunk_id, parent_id, sub_text, chunk_meta))
                    sec_chunk_counter += 1
                    chunk_counter += 1

        return child_chunks, parent_store

    def _split_section_into_chunks(
        self,
        text: str,
        sec_num: str,
        sec_title: str,
        policy_id: str,
        policy_title: str,
        department: str = "General"
    ) -> List[str]:
        """Splits larger sections into overlapping chunks without breaking numbered points or bullets."""
        # Split by paragraph or list boundaries
        units = [u.strip() for u in re.split(r"\n{2,}|\n(?=[•\-\d]+\. )", text) if u.strip()]

        chunks = []
        current_units: List[str] = []
        current_tokens = 0
        header_prefix = f"[{policy_id}: {policy_title} | Department: {department} | Section {sec_num}: {sec_title}]\n"

        for unit in units:
            u_tokens = self.estimate_tokens(unit)
            if current_tokens + u_tokens > self.target_tokens and current_units:
                chunk_content = header_prefix + "\n\n".join(current_units)
                chunks.append(chunk_content)

                # Overlap: keep last 1-2 units if within overlap token budget
                overlap_units = []
                overlap_count = 0
                for rev_unit in reversed(current_units):
                    rev_tokens = self.estimate_tokens(rev_unit)
                    if overlap_count + rev_tokens <= self.overlap_tokens:
                        overlap_units.insert(0, rev_unit)
                        overlap_count += rev_tokens
                    else:
                        break

                current_units = overlap_units
                current_tokens = overlap_count

            current_units.append(unit)
            current_tokens += u_tokens

        if current_units:
            chunk_content = header_prefix + "\n\n".join(current_units)
            chunks.append(chunk_content)

        return chunks

    @staticmethod
    def _build_metadata(
        metadata: Dict[str, Any],
        sec_num: str,
        sec_title: str,
        parent_id: str,
        chunk_id: str
    ) -> Dict[str, Any]:
        """Constructs canonical metadata dict matching Section 7 specifications."""
        return {
            "policy_id": metadata.get("policy_id", ""),
            "policy_title": metadata.get("policy_title", ""),
            "department": metadata.get("department", ""),
            "department_code": metadata.get("department_code", ""),
            "section_number": sec_num,
            "section_title": sec_title,
            "parent_id": parent_id,
            "chunk_id": chunk_id,
            "source_file": metadata.get("source_file", ""),
            "version": metadata.get("version", "1.0"),
            "document_status": metadata.get("status", metadata.get("document_status", "Draft baseline")),
            "status": metadata.get("status", "Draft baseline"),
            "effective_date": metadata.get("effective_date", "2026-11-08"),
            "review_date": metadata.get("review_date", "2027-11-08"),
            "classification": metadata.get("classification", "Internal — Template"),
            "file_type": metadata.get("file_type", "MD"),
        }


policy_chunker = ParentChildSectionChunker()
parent_child_chunker = policy_chunker
