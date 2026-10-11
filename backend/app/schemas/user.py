from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import LocationIn, OutDateTime

__all__ = ["LocationIn", "UserRegister", "UserLogin", "UserOut", "TokenResponse", "ProfileUpdate"]


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["donor", "ngo", "admin"]
    phone: Optional[str] = None
    location: LocationIn
    admin_code: Optional[str] = None  # required only when role == "admin"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = None
    location: Optional[LocationIn] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verified: bool
    created_at: OutDateTime


class TokenResponse(BaseModel):
    token: str
    user: UserOut
