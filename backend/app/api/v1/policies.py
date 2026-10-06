from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.connection import get_db
from backend.app.schemas.policy import PolicyResponse, PolicyVersionResponse, PolicyUpdate
from backend.app.schemas.common import BaseResponse
from backend.app.services.policy_service import policy_service

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.get("/", response_model=BaseResponse[List[PolicyResponse]])
async def list_policies(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    policies = await policy_service.list_policies(db, category=category, status=status)
    return BaseResponse(
        data=[PolicyResponse.model_validate(p) for p in policies],
        message="Policies retrieved successfully"
    )

@router.get("/{policy_id}", response_model=BaseResponse[PolicyResponse])
async def get_policy_detail(
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    policy = await policy_service.get_policy(db, policy_id)
    return BaseResponse(data=PolicyResponse.model_validate(policy), message="Policy retrieved")

@router.get("/{policy_id}/versions", response_model=BaseResponse[List[PolicyVersionResponse]])
async def get_policy_versions(
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    versions = await policy_service.get_policy_versions(db, policy_id)
    return BaseResponse(
        data=[PolicyVersionResponse.model_validate(v) for v in versions],
        message="Versions retrieved"
    )

@router.put("/{policy_id}", response_model=BaseResponse[PolicyResponse])
async def update_policy(
    policy_id: int,
    update_data: PolicyUpdate,
    db: AsyncSession = Depends(get_db)
):
    policy = await policy_service.update_policy(db, policy_id, update_data)
    return BaseResponse(data=PolicyResponse.model_validate(policy), message="Policy updated")

@router.delete("/{policy_id}", response_model=BaseResponse[dict])
async def delete_policy(
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    await policy_service.delete_policy(db, policy_id)
    return BaseResponse(data={"deleted_policy_id": policy_id}, message="Policy and vector chunks deleted")
