from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from core.database import Base


class AlertFollowup(Base):
    __tablename__ = "alert_followups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(String, index=True)
    action_type = Column(String, default="跟进")
    content = Column(Text, default="")
    operator = Column(String, default="")
    result_status = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
