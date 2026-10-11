from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.donation import Donation
from app.models.requirement import Requirement
from app.services.recommender import recommend

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("/")
def get_recommendations(db: Session = Depends(get_db)):
    donations = db.query(Donation).all()
    requirements = db.query(Requirement).all()
    recs = recommend(donations, requirements)
    return recs

@router.get("/with-urgency")
def get_recommendations_with_urgency(db: Session = Depends(get_db)):
    donations = db.query(Donation).all()
    requirements = db.query(Requirement).all()
    recs = recommend(donations, requirements)
    return recs
