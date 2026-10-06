from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ChunkMetadata(BaseModel):
    chunk_id: str
    policy_id: int
    policy_name: str
    category: str
    department: str
    version: str = "1.0"
    status: str = "active"  # active, archived
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    page: int = 1
    section: str = "General"
    token_count: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)

    def to_payload(self) -> dict:
        return self.model_dump()
