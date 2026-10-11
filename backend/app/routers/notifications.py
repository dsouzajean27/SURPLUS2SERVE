from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationOut
from app.services.donations import scan_expiry_warnings

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(unread_only: bool = False, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    scan_expiry_warnings(db, current_user)  # adds 'approaching expiry' alerts lazily
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.read == False)  # noqa: E712
    return q.order_by(Notification.created_at.desc()).limit(100).all()


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.user_id == current_user.id,
                                      Notification.read == False).count()  # noqa: E712
    return {"unread": n}


@router.patch("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id,
                                  Notification.read == False).update({"read": True})  # noqa: E712
    db.commit()
    return {"status": "ok"}


@router.patch("/{notif_id}/read")
def mark_as_read(notif_id: str, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notif_id,
                                      Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read = True
    db.commit()
    return {"status": "read"}
