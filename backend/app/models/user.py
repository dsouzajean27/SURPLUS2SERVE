import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, Float, Enum
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("donor", "ngo", "admin", name="user_role"), nullable=False)
    phone = Column(String(30), nullable=True)

    # Location fields - stored directly on the user so donor/NGO profile
    # location can be reused when posting donations/requirements.
    address = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    verified = Column(Boolean, default=False)  # admins auto-verified, donor/ngo need admin approval
    created_at = Column(DateTime, default=datetime.utcnow)

    donations = relationship("Donation", back_populates="donor", foreign_keys="Donation.donor_id")
    requirements = relationship("Requirement", back_populates="ngo", foreign_keys="Requirement.ngo_id")
