from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar, List

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[Any] = None

class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    pages: int
