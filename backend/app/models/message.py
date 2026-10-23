import uuid
from app.utils.timeutil import utcnow

from sqlalchemy import Column, String, DateTime, ForeignKey, Text

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Message(Base):
    """In-app chat message between a donor and the NGO that accepted their donation."""

    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
