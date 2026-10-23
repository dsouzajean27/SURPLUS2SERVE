import re
from typing import Optional, Literal, List

from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.schemas.common import LocationIn, InDateTime, OutDateTime

Status = Literal["posted", "accepted", "pickup_pending", "delivered", "completed", "expired"]


Packaging = Literal["sealed", "covered", "open"]


class HygieneChecklist(BaseModel):
    """Donor's food-safety declaration (Phase 5). Keys match services/quality.CHECKLIST_LABELS."""
    hygienic_prep: bool
    not_plate_leftovers: bool
    stored_properly: bool
    clean_container: bool
    no_spoilage_signs: bool


class QualityOut(BaseModel):
    score: int
    status: str            # good | caution | rejected
    notes: List[str] = []
    blockers: List[str] = []


class InspectionOut(BaseModel):
    result: str            # passed | failed
    notes: Optional[str] = None
    temperature_c: Optional[float] = None
    inspected_at: Optional[OutDateTime] = None


class InspectionIn(BaseModel):
    """Recipient's check when collecting the food."""
    result: Literal["passed", "failed"]
    temperature_c: Optional[float] = Field(default=None, ge=-60, le=120)
    notes: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _need_reason(self):
        if self.result == "failed" and not (self.notes and self.notes.strip()):
            raise ValueError("notes are required when a quality check fails - say what is wrong")
        return self


class QualityPreviewIn(BaseModel):
    """Lets the post-donation form show the quality score before the donor submits."""
    food_type: str = Field(default="", max_length=150)
    storage_condition: Literal["room_temp", "refrigerated", "frozen"] = "room_temp"
    prep_time: Optional[InDateTime] = None
    expiry_time: InDateTime
    packaging: Optional[Packaging] = None
    hygiene_checklist: Optional[HygieneChecklist] = None
    has_photo: bool = False


class DonationCreate(BaseModel):
    food_type: str = Field(min_length=1, max_length=150)
    quantity_kg: float = Field(gt=0)
    servings: float = Field(gt=0)
    prep_time: Optional[InDateTime] = None
    expiry_time: InDateTime
    storage_condition: Literal["room_temp", "refrigerated", "frozen"] = "room_temp"
    location: LocationIn
    image_url: Optional[str] = Field(default=None, max_length=500)
    allergens: Optional[str] = Field(default=None, max_length=255)
    packaging: Optional[Packaging] = None
    hygiene_checklist: Optional[HygieneChecklist] = None

    @field_validator("image_url")
    @classmethod
    def validate_image_url(cls, value):
        """Accept ordinary HTTP(S) image URLs or an image uploaded through our own
        /api/uploads/food-image route; do not allow javascript:/data: URLs."""
        if value is None or not value.strip():
            return None
        value = value.strip()
        # image uploaded to this app, e.g. /uploads/3f9c1a....jpg (only our generated names)
        if re.fullmatch(r"/uploads/[A-Za-z0-9]+\.(jpg|png|webp)", value):
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("image_url must be a valid http:// or https:// URL")
        return value

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
    allergens: Optional[str] = Field(default=None, max_length=255)
    packaging: Optional[Packaging] = None
    hygiene_checklist: Optional[HygieneChecklist] = None


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
    allergens: Optional[str] = None
    packaging: Optional[str] = None
    hygiene_checklist: Optional[dict] = None
    quality: Optional[QualityOut] = None
    inspection: Optional[InspectionOut] = None
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
