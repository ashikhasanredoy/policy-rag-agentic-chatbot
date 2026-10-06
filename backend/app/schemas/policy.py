from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PolicyVersionBase(BaseModel):
    version: str
    file_name: Optional[str] = None
    file_size: Optional[int] = 0
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: str = "active"
    changelog: Optional[str] = None
    created_by: Optional[str] = None

class PolicyVersionCreate(PolicyVersionBase):
    policy_id: int
    file_path: Optional[str] = None

class PolicyVersionResponse(PolicyVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    created_at: datetime

class PolicyBase(BaseModel):
    name: str
    category: str
    department: str
    description: Optional[str] = None
    status: str = "active"

class PolicyCreate(PolicyBase):
    initial_version: str = "1.0"
    content: Optional[str] = None

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class PolicyResponse(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    current_version: str
    created_at: datetime
    updated_at: datetime
    versions: List[PolicyVersionResponse] = []
