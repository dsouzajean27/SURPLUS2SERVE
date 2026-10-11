from datetime import datetime
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, PlainSerializer, model_validator

from app.utils.timeutil import to_naive_utc

# Incoming: any ISO datetime -> naive UTC.  Outgoing: ISO string with a trailing 'Z'
# so the browser always knows it is UTC and can show it in local time.
InDateTime = Annotated[datetime, AfterValidator(to_naive_utc)]
OutDateTime = Annotated[datetime, PlainSerializer(lambda d: d.isoformat() + "Z", return_type=str)]


class LocationIn(BaseModel):
    """Address is required. lat/lng are optional: if missing, the backend
    geocodes the address (OpenStreetMap Nominatim) in the background."""

    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None

    @model_validator(mode="after")
    def _check(self):
        if not self.address or not self.address.strip():
            raise ValueError("address is required")
        if (self.lat is None) != (self.lng is None):
            raise ValueError("provide both lat and lng, or neither")
        if self.lat is not None and not (-90 <= self.lat <= 90 and -180 <= self.lng <= 180):
            raise ValueError("lat/lng out of range")
        return self
