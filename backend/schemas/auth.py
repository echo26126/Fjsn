from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    roles: List[str] = ["viewer"]

class UserLogin(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    is_active: bool
    roles: List[str]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
