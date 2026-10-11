from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import LocationIn, InDateTime, OutDateTime

Status = Literal["posted", "accepted", "pickup_pending", "delivered", "completed", "expired"]


class DonationCreate(BaseModel):
    food_type: str = Field(min_length=1, max_length=150)
    quantity_kg: float = Field(gt=0)
    servings: float = Field(gt=0)
    prep_time: Optional[InDateTime] = None
    expiry_time: InDateTime
    storage_condition: Literal["room_temp", "refrigerated", "frozen"] = "room_temp"
    location: LocationIn
    image_url: Optional[str] = None

    @model_validator(mode="after")
    def _times(self):
        if self.prep_time and self.prep_time >= self.expiry_time:
            raise ValueError("expiry_time must be after prep_time")
        return self


class DonationUpdate(BaseModel):
    food_type: Optional[str] = Field(default=None, min_length=1, max_length=150)
    quantity_kg: Optional[float] = Field(default=None, gt=0)
    servings: Optional[float] = Field(default=None, gt=0)
    prep_time: Optional[InDateTime] = None
    expiry_time: Optional[InDateTime] = None
    storage_condition: Optional[Literal["room_temp", "refrigerated", "frozen"]] = None
    location: Optional[LocationIn] = None


class StatusUpdate(BaseModel):
    status: Status
    ngo_id: Optional[str] = None  # only an admin may accept on behalf of another NGO
    note: Optional[str] = None


class DonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    donor_id: str
    donor_name: Optional[str] = None
    food_type: str
    quantity_kg: float
    servings: float
    prep_time: Optional[OutDateTime] = None
    expiry_time: OutDateTime
    storage_condition: str
    address: str
    latitude: float
    longitude: float
    image_url: Optional[str] = None
    status: str
    fallback_recommendation: str
    accepted_ngo_id: Optional[str] = None
    accepted_ngo_name: Optional[str] = None
    created_at: OutDateTime
    # computed fields
    urgency: str = "low"
    hours_left: float = 0
    urgency_reason: str = ""
    distance_km: Optional[float] = None


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    note: Optional[str] = None
    changed_at: OutDateTime
