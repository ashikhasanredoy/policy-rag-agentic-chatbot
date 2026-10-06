import uuid
from typing import List, Dict, Any
from backend.app.rag.cleaner import clean_text, extract_sections
from backend.app.rag.metadata import ChunkMetadata

class DocumentChunk:
    def __init__(self, text: str, metadata: ChunkMetadata):
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "metadata": self.metadata.to_payload()
        }

class PolicyChunker:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_policy_document(
        self,
        full_text: str,
        policy_id: int,
        policy_name: str,
        category: str,
        department: str,
        version: str = "1.0",
        status: str = "active",
        effective_date: str = "2026-01-01",
        page_texts: List[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Chunks text with section awareness and page tracking.
        page_texts is optional: [{"page_number": 1, "text": "..."}]
        """
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        # If page-level breakdown is available, process page by page
        if page_texts:
            for item in page_texts:
                page_num = item.get("page_number", 1)
                text = item.get("text", "")
                sections = extract_sections(text)
                for sec in sections:
                    sec_title = sec["section_title"]
                    sec_content = sec["content"]
                    sub_chunks = self._sliding_window_split(sec_content)
                    for text_segment in sub_chunks:
                        chunk_idx += 1
                        meta = ChunkMetadata(
                            chunk_id=f"pol_{policy_id}_v{version}_{chunk_idx:04d}",
                            policy_id=policy_id,
                            policy_name=policy_name,
                            category=category,
                            department=department,
                            version=version,
                            status=status,
                            effective_date=effective_date,
                            page=page_num,
                            section=sec_title,
                            token_count=len(text_segment.split())
                        )
                        chunks.append(DocumentChunk(text=text_segment, metadata=meta))
        else:
            # Full text without page breakdown
            sections = extract_sections(full_text)
            for sec in sections:
                sec_title = sec["section_title"]
                sec_content = sec["content"]
                sub_chunks = self._sliding_window_split(sec_content)
                for text_segment in sub_chunks:
                    chunk_idx += 1
                    meta = ChunkMetadata(
                        chunk_id=f"pol_{policy_id}_v{version}_{chunk_idx:04d}",
                        policy_id=policy_id,
                        policy_name=policy_name,
                        category=category,
                        department=department,
                        version=version,
                        status=status,
                        effective_date=effective_date,
                        page=1,
                        section=sec_title,
                        token_count=len(text_segment.split())
                    )
                    chunks.append(DocumentChunk(text=text_segment, metadata=meta))

        return chunks

    def _sliding_window_split(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []
        if len(words) <= self.chunk_size:
            return [text.strip()]

        result = []
        start = 0
        step = max(1, self.chunk_size - self.chunk_overlap)
        while start < len(words):
            end = min(len(words), start + self.chunk_size)
            chunk_words = words[start:end]
            result.append(" ".join(chunk_words))
            if end == len(words):
                break
            start += step

        return result
