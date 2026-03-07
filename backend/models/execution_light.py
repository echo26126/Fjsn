from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text

from core.database import Base


class ExecutionLight(Base):
    __tablename__ = "executions_light"

    execution_id = Column(String, primary_key=True, index=True)
    recommendation_id = Column(String, index=True)
    status = Column(String, default="待确认", index=True)
    owner = Column(String, default="")
    plan_qty_ton = Column(Float, default=0)
    actual_qty_ton = Column(Float, default=0)
    due_date = Column(String, default="")
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
