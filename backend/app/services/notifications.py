from app.models.notification import Notification
from app.database import SessionLocal
from datetime import datetime

def create_notification(db: SessionLocal, user_id: int, message: str):
    notif = Notification(user_id=user_id, message=message, created_at=datetime.now(), read=False)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif
