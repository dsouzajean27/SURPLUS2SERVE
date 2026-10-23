import uuid
from app.utils.timeutil import utcnow

from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Donation(Base):
    __tablename__ = "donations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    donor_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    food_type = Column(String(150), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    servings = Column(Float, nullable=False)

    prep_time = Column(DateTime, nullable=True)
    expiry_time = Column(DateTime, nullable=False)
    storage_condition = Column(
        Enum("room_temp", "refrigerated", "frozen", name="storage_condition"),
        default="room_temp",
    )

    address = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    image_url = Column(String(500), nullable=True)

    # ---- Phase 5: food quality verification --------------------------------
    allergens = Column(String(255), nullable=True)           # free text, e.g. "nuts, dairy"
    packaging = Column(String(20), nullable=True)            # sealed | covered | open
    hygiene_checklist = Column(JSON, nullable=True)          # donor's safety declaration
    # Recipient's inspection at pickup
    inspection_result = Column(String(10), nullable=True)    # passed | failed
    inspection_notes = Column(Text, nullable=True)
    inspection_temp_c = Column(Float, nullable=True)
    inspected_at = Column(DateTime, nullable=True)

    status = Column(
        Enum(
            "posted", "accepted", "pickup_pending", "delivered", "completed", "expired",
            name="donation_status",
        ),
        default="posted",
    )
    # Circular-economy fallback: set when no suitable human-consumption
    # recipient is found, suggesting an alternate recovery route instead.
    fallback_recommendation = Column(
        Enum("compost", "animal_feed", "none", name="fallback_type"),
        default="none",
    )

    accepted_ngo_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=utcnow)

    donor = relationship("User", back_populates="donations", foreign_keys=[donor_id])
    accepted_ngo = relationship("User", foreign_keys=[accepted_ngo_id])
    status_history = relationship(
        "DonationStatusHistory", back_populates="donation", cascade="all, delete-orphan"
    )


class DonationStatusHistory(Base):
    """Keeps an audit trail of every status change for a donation (FR10)."""

    __tablename__ = "donation_status_history"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    donation_id = Column(String(36), ForeignKey("donations.id"), nullable=False)
    status = Column(String(30), nullable=False)
    note = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=utcnow)

    donation = relationship("Donation", back_populates="status_history")
