import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Requirement(Base):
    """An NGO/food bank's stated food need (FR04)."""

    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    ngo_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    food_type = Column(String(150), nullable=False)  # "any" matches all donation types
    required_quantity_kg = Column(Float, nullable=False)

    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    urgency = Column(Enum("low", "medium", "high", name="requirement_urgency"), nullable=False)
    deadline = Column(DateTime, nullable=True)
    pickup_availability = Column(
        Enum("immediate", "within_2h", "later_today", "flexible", name="pickup_availability"),
        default="flexible",
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    ngo = relationship("User", back_populates="requirements", foreign_keys=[ngo_id])
