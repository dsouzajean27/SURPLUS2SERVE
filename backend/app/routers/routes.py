from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.donation import Donation
from app.utils.geo import sort_by_distance

router = APIRouter(prefix="/api/routes", tags=["routes"])

@router.get("/donor/{donor_id}")
def get_pickup_route(donor_id: int, db: Session = Depends(get_db)):
    donations = db.query(Donation).filter(Donation.donor_id == donor_id).all()
    if not donations:
        return {"message": "No donations found"}
    
    origin = (donations[0].lat, donations[0].lng)
    points = [(d.lat, d.lng, d.id) for d in donations]
    route = sort_by_distance(origin[0], origin[1], points)
    return {"pickup_order": route}
