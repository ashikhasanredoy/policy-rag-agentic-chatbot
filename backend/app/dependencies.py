from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.connection import get_db
from backend.app.database.repository import UserRepository
from backend.app.database.models import User
from backend.app.core.security import decode_access_token
from backend.app.core.exceptions import InvalidCredentialsException, InsufficientPermissionsException

security = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = int(payload["sub"])
    user_repo = UserRepository(db)
    return await user_repo.get_by_id(user_id)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise InvalidCredentialsException()
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise InvalidCredentialsException()
    user_id = int(payload["sub"])
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise InvalidCredentialsException()
    return user

def require_role(allowed_roles: list):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise InsufficientPermissionsException()
        return current_user
    return role_checker
