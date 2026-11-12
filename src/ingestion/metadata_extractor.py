"""
Metadata Extractor and Validator for Enterprise Policies.
Enriches parsed policy documents with canonical metadata from Policy_Register.csv.
"""

import csv
from pathlib import Path
from typing import Dict, Any, Optional
from src.config.settings import settings


class MetadataRegistry:
    """Master registry loaded from Policy_Register.csv."""

    def __init__(self, register_path: Optional[Path] = None):
        self.register_path = register_path or settings.REGISTER_CSV
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.title_to_id: Dict[str, str] = {}
        self._load()

    def _load(self):
        if not self.register_path.exists():
            return

        with open(self.register_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("Policy ID", "").strip()
                if not pid:
                    continue
                dept = row.get("Department", "").strip()
                title = row.get("Policy Title", "").strip()
                dept_code = pid.split("-")[0] if "-" in pid else ""

                entry = {
                    "policy_id": pid,
                    "policy_title": title,
                    "department": dept,
                    "department_code": dept_code,
                    "owner": row.get("Policy Owner", "").strip(),
                    "approver": row.get("Approval Authority", "").strip(),
                    "version": row.get("Version", "1.0").strip(),
                    "effective_date": row.get("Effective Date", "").replace(" (placeholder)", "").strip(),
                    "review_date": row.get("Next Review", "").replace(" (placeholder)", "").strip(),
                    "status": row.get("Status", "Draft baseline").strip(),
                    "docx_file": row.get("DOCX File", "").strip(),
                    "pdf_file": row.get("PDF File", "").strip(),
                }
                self.registry[pid] = entry
                self.title_to_id[title.lower()] = pid

    def get_metadata(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(policy_id)

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(policy_id)

    def get_all_policies(self) -> Dict[str, Dict[str, Any]]:
        return self.registry

    def enrich(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Merges document-extracted metadata with canonical Policy_Register metadata."""
        pid = raw_metadata.get("policy_id", "").strip()
        reg_entry = self.registry.get(pid, {})

        enriched = dict(raw_metadata)
        if reg_entry:
            for k in [
                "policy_id", "policy_title", "department", "department_code",
                "owner", "approver", "version", "effective_date", "review_date", "status"
            ]:
                if reg_entry.get(k):
                    enriched[k] = reg_entry[k]

        return enriched

    def validate(self, metadata: Dict[str, Any]) -> bool:
        """Validates that critical metadata fields are present."""
        required = ["policy_id", "policy_title", "department"]
        return all(bool(metadata.get(f)) for f in required)


metadata_registry = MetadataRegistry()
