"""In-app notifications (FR13) + optional e-mail via SMTP."""
import smtplib
from email.message import EmailMessage
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import Notification
from app.models.user import User


def _send_email(to_addr: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        return
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to_addr, subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=8) as s:
            s.starttls()
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
    except Exception:
        pass  # e-mail is best-effort; the in-app notification is the source of truth


def create_notification(db: Session, user_id: str, message: str, type: str = "info",
                        donation_id: Optional[str] = None, commit: bool = True) -> Notification:
    notif = Notification(user_id=user_id, message=message, type=type,
                         related_donation_id=donation_id, read=False)
    db.add(notif)
    if commit:
        db.commit()
        db.refresh(notif)
    user = db.get(User, user_id)
    if user and settings.SMTP_HOST:
        _send_email(user.email, f"Surplus2Serve: {type.replace('_', ' ')}", message)
    return notif


def notify_status_change(db: Session, donation, new_status: str, actor_id: str) -> None:
    labels = {
        "accepted": "was accepted",
        "pickup_pending": "is ready for pickup",
        "delivered": "has been delivered",
        "completed": "is completed - thank you!",
        "expired": "has expired",
    }
    ngo_name = donation.accepted_ngo.name if donation.accepted_ngo else "a recipient"
    msg = f"Donation '{donation.food_type}' ({donation.quantity_kg:g} kg) {labels.get(new_status, new_status)}"
    if new_status == "accepted":
        msg += f" by {ngo_name}"
    msg += "."
    kind = "accepted" if new_status == "accepted" else ("expiry_warning" if new_status == "expired" else "status_change")
    for uid in {donation.donor_id, donation.accepted_ngo_id} - {None, actor_id}:
        create_notification(db, uid, msg, kind, donation.id, commit=False)
    db.commit()
