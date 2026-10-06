from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.models import Policy, PolicyVersion
from backend.app.database.repository import PolicyRepository
from backend.app.schemas.policy import PolicyCreate, PolicyUpdate
from backend.app.core.exceptions import PolicyNotFoundException

class PolicyService:
    async def list_policies(self, db: AsyncSession, category: Optional[str] = None, status: Optional[str] = None) -> List[Policy]:
        repo = PolicyRepository(db)
        return await repo.get_all(category=category, status=status)

    async def get_policy(self, db: AsyncSession, policy_id: int) -> Policy:
        repo = PolicyRepository(db)
        policy = await repo.get_by_id(policy_id)
        if not policy:
            raise PolicyNotFoundException(policy_id)
        return policy

    async def get_policy_versions(self, db: AsyncSession, policy_id: int) -> List[PolicyVersion]:
        repo = PolicyRepository(db)
        return await repo.get_versions(policy_id)

    async def update_policy(self, db: AsyncSession, policy_id: int, update_data: PolicyUpdate) -> Policy:
        repo = PolicyRepository(db)
        data = {k: v for k, v in update_data.model_dump().items() if v is not None}
        policy = await repo.update(policy_id, **data)
        if not policy:
            raise PolicyNotFoundException(policy_id)
        return policy

    async def delete_policy(self, db: AsyncSession, policy_id: int) -> bool:
        repo = PolicyRepository(db)
        from backend.app.rag.qdrant_store import qdrant_store
        qdrant_store.delete_by_policy_id(policy_id)
        return await repo.delete(policy_id)

policy_service = PolicyService()
