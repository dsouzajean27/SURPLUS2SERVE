from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.user import LocationIn


class DonationCreate(BaseModel):
    food_type: str = Field(min_length=1, max_length=150)
    quantity_kg: float = Field(gt=0)
    servings: float = Field(gt=0)
    prep_time: Optional[datetime] = None
    expiry_time: datetime
    storage_condition: Literal["room_temp", "refrigerated", "frozen"] = "room_temp"
    location: LocationIn
    image_url: Optional[str] = None


class StatusUpdate(BaseModel):
    status: Literal["posted", "accepted", "pickup_pending", "delivered", "completed", "expired"]
    ngo_id: Optional[str] = None  # required when status == "accepted"
    note: Optional[str] = None


class DonorOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True


class DonationOut(BaseModel):
    id: str
    donor_id: str
    food_type: str
    quantity_kg: float
    servings: float
    prep_time: Optional[datetime] = None
    expiry_time: datetime
    storage_condition: str
    address: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    status: str
    fallback_recommendation: str
    accepted_ngo_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
