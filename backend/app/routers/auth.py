from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserOut, ProfileUpdate
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.services.location import resolve_location

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if payload.role == "admin" and payload.admin_code != settings.ADMIN_SIGNUP_CODE:
        raise HTTPException(status_code=403, detail="Invalid admin sign-up code")

    address, lat, lng = resolve_location(payload.location)
    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        phone=payload.phone,
        address=address,
        latitude=lat,
        longitude=lng,
        verified=(payload.role == "admin"),  # admins auto-verified; donor/ngo are verified by an admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token({"sub": user.id, "role": user.role, "name": user.name})
    return TokenResponse(token=token, user=user)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(payload: ProfileUpdate, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    """Profile management (FR02)."""
    if payload.name:
        current_user.name = payload.name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.location:
        current_user.address, current_user.latitude, current_user.longitude = resolve_location(payload.location)
    db.commit()
    db.refresh(current_user)
    return current_user
