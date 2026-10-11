from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/")
def list_notifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(Notification).filter(Notification.user_id == user_id).all()

@router.post("/")
def send_notification(user_id: int, message: str, db: Session = Depends(get_db)):
    return create_notification(db, user_id, message)

@router.patch("/{notif_id}/read")
def mark_as_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).get(notif_id)
    notif.read = True
    db.commit()
    return {"status": "read"}
