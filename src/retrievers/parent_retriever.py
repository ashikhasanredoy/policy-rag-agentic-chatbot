"""
Parent Document Lookup Engine.
Stores and resolves complete policy sections using parent_id references
from retrieved child chunks.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.config.settings import settings


class ParentDocumentRetriever:
    """Provides fast O(1) lookup of parent section text from child chunks."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (settings.PROCESSED_DATA_DIR / "parent_sections.json")
        self.parent_store: Dict[str, str] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.parent_store = json.load(f)
            except Exception as e:
                print(f"Notice: Could not load parent store ({e})")

    def save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.parent_store, f, ensure_ascii=False, indent=2)

    def add_parent_sections(self, parent_dict: Dict[str, str]):
        self.parent_store.update(parent_dict)

    def get_parent_text(self, parent_id: str) -> Optional[str]:
        return self.parent_store.get(parent_id)

    def enrich_candidate_with_parent(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Adds parent section text to candidate dict if available."""
        parent_id = candidate.get("metadata", {}).get("parent_id")
        if parent_id and parent_id in self.parent_store:
            candidate["parent_text"] = self.parent_store[parent_id]
        else:
            candidate["parent_text"] = candidate.get("text", "")
        candidate["parent_section_text"] = candidate["parent_text"]
        return candidate


parent_retriever = ParentDocumentRetriever()
