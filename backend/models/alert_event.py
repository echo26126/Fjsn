from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text

from core.database import Base


class AlertEvent(Base):
    __tablename__ = "alert_events"

    alert_id = Column(String, primary_key=True, index=True)
    alert_level = Column(String, default="P2", index=True)
    alert_type = Column(String, default="履约风险", index=True)
    alert_status = Column(String, default="新建", index=True)
    source_type = Column(String, default="auto", index=True)
    alert_title = Column(String, default="")
    alert_content = Column(Text, default="")
    severity_tag = Column(String, default="警告")
    context_json = Column(Text, default="")
    affected_org_name = Column(String, default="")
    sku_name = Column(String, default="")
    gap_qty_ton = Column(Float, default=0)
    fulfillment_rate_pred = Column(Float, default=0)
    recommendation_ref_id = Column(String, default="", index=True)
    owner_user = Column(String, default="")
    assignee_user = Column(String, default="")
    process_status = Column(String, default="待跟进", index=True)
    process_result = Column(Text, default="")
    action_deadline = Column(String, default="")
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
