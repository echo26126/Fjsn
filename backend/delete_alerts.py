from core.database import SessionLocal
from models.alert_event import AlertEvent
from models.recommendation import Recommendation
from models.alert_followup import AlertFollowup

def delete_specific_alerts():
    db = SessionLocal()
    titles = [
        "宁德基地高库存预警",
        "莆田基地磨机效率偏低",
        "泉州基地熟料线停机风险"
    ]
    
    try:
        # Find the alerts
        alerts = db.query(AlertEvent).filter(AlertEvent.alert_title.in_(titles)).all()
        alert_ids = [a.alert_id for a in alerts]
        
        if not alert_ids:
            print("No matching alerts found.")
            return

        print(f"Found {len(alert_ids)} alerts to delete: {alert_ids}")

        # Delete associated recommendations
        recs_deleted = db.query(Recommendation).filter(Recommendation.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        print(f"Deleted {recs_deleted} associated recommendations.")

        # Delete associated followups
        followups_deleted = db.query(AlertFollowup).filter(AlertFollowup.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        print(f"Deleted {followups_deleted} associated followups.")

        # Delete the alerts themselves
        alerts_deleted = db.query(AlertEvent).filter(AlertEvent.alert_id.in_(alert_ids)).delete(synchronize_session=False)
        print(f"Deleted {alerts_deleted} alerts.")

        db.commit()
        print("Successfully committed deletions.")
    except Exception as e:
        db.rollback()
        print(f"Error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_specific_alerts()
