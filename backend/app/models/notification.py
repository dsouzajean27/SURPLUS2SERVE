import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Notification(Base):
    """In-app notifications for users (FR13) - new donation matches,
    acceptance, pickup reminders, status changes, approaching expiry."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="info")  # e.g. new_match, accepted, status_change, expiry_warning
    related_donation_id = Column(String(36), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
