from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.donation import Donation
from app.models.requirement import Requirement

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/impact")
def impact_dashboard(db: Session = Depends(get_db)):
    total_donations = db.query(Donation).count()
    completed = db.query(Donation).filter(Donation.status == "Completed").count()
    expired = db.query(Donation).filter(Donation.status == "Expired").count()
    total_requirements = db.query(Requirement).count()

    return {
        "total_donations": total_donations,
        "completed_donations": completed,
        "expired_donations": expired,
        "total_requirements": total_requirements,
        "completion_rate": round(completed / total_donations * 100, 1) if total_donations else 0
    }

@router.get("/ngo/{ngo_id}")
def ngo_dashboard(ngo_id: int, db: Session = Depends(get_db)):
    posted = db.query(Requirement).filter(Requirement.ngo_id == ngo_id).count()
    fulfilled = db.query(Donation).filter(Donation.accepted_by == ngo_id, Donation.status == "Completed").count()
    return {
        "requirements_posted": posted,
        "requirements_fulfilled": fulfilled
    }

