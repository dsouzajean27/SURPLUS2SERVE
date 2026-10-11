from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import LocationIn, InDateTime, OutDateTime


class RequirementCreate(BaseModel):
    food_type: str = Field(min_length=1, max_length=150)  # "any" matches every donation type
    required_quantity_kg: float = Field(gt=0)
    location: Optional[LocationIn] = None  # defaults to the NGO's profile location
    urgency: Literal["low", "medium", "high"]
    deadline: Optional[InDateTime] = None
    pickup_availability: Literal["immediate", "within_2h", "later_today", "flexible"] = "flexible"


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ngo_id: str
    ngo_name: Optional[str] = None
    food_type: str
    required_quantity_kg: float
    address: str
    latitude: float
    longitude: float
    urgency: str
    deadline: Optional[OutDateTime] = None
    pickup_availability: str
    created_at: OutDateTime
