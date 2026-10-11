from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field


class LocationIn(BaseModel):
    address: str
    lat: float
    lng: float


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["donor", "ngo", "admin"]
    phone: Optional[str] = None
    location: LocationIn


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    token: str
    user: UserOut
