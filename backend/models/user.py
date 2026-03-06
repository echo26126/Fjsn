from sqlalchemy import Boolean, Column, Integer, String, JSON
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    roles = Column(JSON, default=[]) # 存储角色列表，如 ["admin", "analyst"]
