from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.user import LocationIn


class RequirementCreate(BaseModel):
    food_type: str = Field(min_length=1, max_length=150)  # "any" matches every donation type
    required_quantity_kg: float = Field(gt=0)
    location: LocationIn
    urgency: Literal["low", "medium", "high"]
    deadline: Optional[datetime] = None
    pickup_availability: Literal["immediate", "within_2h", "later_today", "flexible"] = "flexible"


class RequirementOut(BaseModel):
    id: str
    ngo_id: str
    food_type: str
    required_quantity_kg: float
    address: str
    latitude: float
    longitude: float
    urgency: str
    deadline: Optional[datetime] = None
    pickup_availability: str
    created_at: datetime

    class Config:
        from_attributes = True
