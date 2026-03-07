from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text

from core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(String, primary_key=True, index=True)
    alert_id = Column(String, index=True)
    recommendation_role = Column(String, default="PRIMARY", index=True)
    recommendation_summary = Column(Text, default="")
    action_type = Column(String, default="")
    from_org_name = Column(String, default="")
    to_org_name = Column(String, default="")
    action_qty_ton = Column(Float, default=0)
    est_net_gain = Column(Float, default=0)
    decision_status = Column(String, default="待确认", index=True)
    decision_reason = Column(Text, default="")
    decision_user = Column(String, default="")
    decision_time = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
