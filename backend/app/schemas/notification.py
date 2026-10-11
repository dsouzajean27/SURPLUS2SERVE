from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.common import OutDateTime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    message: str
    type: str
    related_donation_id: Optional[str] = None
    read: bool
    created_at: OutDateTime
