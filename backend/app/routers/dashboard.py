from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.services.impact import impact_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/impact")
def impact_dashboard(db: Session = Depends(get_db)):
    """Platform-wide impact metrics. Public - contains only aggregate numbers."""
    data = impact_summary(db)
    data["total_requirements"] = db.query(Requirement).count()
    return data


@router.get("/donor")
def donor_dashboard(db: Session = Depends(get_db), current_user: User = Depends(require_role("donor"))):
    return impact_summary(db, donor_id=current_user.id)


@router.get("/ngo")
def ngo_dashboard(db: Session = Depends(get_db), current_user: User = Depends(require_role("ngo"))):
    data = impact_summary(db, ngo_id=current_user.id)
    data["requirements_posted"] = db.query(Requirement).filter(Requirement.ngo_id == current_user.id).count()
    data["donations_received"] = data.pop("completed_donations")
    return data
