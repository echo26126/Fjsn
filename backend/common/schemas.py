from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: int = Field(default=200, description="响应状态码")
    msg: str = Field(default="success", description="响应信息")
    data: Optional[T] = Field(default=None, description="响应数据")

class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
