from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.donation import Donation, DonationStatusHistory
from app.models.requirement import Requirement
from app.models.user import User
from app.schemas.user import UserOut
from app.services.impact import impact_summary

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = require_role("admin")


@router.get("/overview")
def overview(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    """FR15 - users, donations, recipients, statuses and recent system activity."""
    users_by_role = dict(db.query(User.role, func.count(User.id)).group_by(User.role).all())
    by_status = dict(db.query(Donation.status, func.count(Donation.id)).group_by(Donation.status).all())
    recent = (db.query(DonationStatusHistory, Donation)
              .join(Donation, Donation.id == DonationStatusHistory.donation_id)
              .order_by(DonationStatusHistory.changed_at.desc()).limit(15).all())
    return {
        "impact": impact_summary(db),
        "users_by_role": users_by_role,
        "unverified_users": db.query(User).filter(User.verified == False, User.role != "admin").count(),  # noqa: E712
        "donations_by_status": by_status,
        "total_requirements": db.query(Requirement).count(),
        "recent_activity": [
            {"donation_id": d.id, "food_type": d.food_type, "status": h.status, "note": h.note,
             "at": h.changed_at.isoformat() + "Z"} for h, d in recent],
    }


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/verify", response_model=UserOut)
def set_verified(user_id: str, verified: bool = True, db: Session = Depends(get_db),
                 _: User = Depends(admin_only)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.verified = verified
    db.commit()
    db.refresh(u)
    return u
