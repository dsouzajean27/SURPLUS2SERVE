from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate, RequirementOut
from app.auth.dependencies import get_current_user, require_role
from app.services.location import resolve_location

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


def _out(r: Requirement) -> dict:
    return {
        "id": r.id, "ngo_id": r.ngo_id, "ngo_name": r.ngo.name if r.ngo else None,
        "food_type": r.food_type, "required_quantity_kg": r.required_quantity_kg,
        "address": r.address, "latitude": r.latitude, "longitude": r.longitude,
        "urgency": r.urgency, "deadline": r.deadline,
        "pickup_availability": r.pickup_availability, "created_at": r.created_at,
    }


@router.post("", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_requirement(payload: RequirementCreate, db: Session = Depends(get_db),
                       current_user: User = Depends(require_role("ngo"))):
    if payload.location:
        address, lat, lng = resolve_location(payload.location)
    elif current_user.latitude is not None:  # default to the NGO's profile location
        address, lat, lng = current_user.address or "", current_user.latitude, current_user.longitude
    else:
        raise HTTPException(status_code=422, detail="location is required")
    r = Requirement(
        ngo_id=current_user.id, food_type=payload.food_type.strip(),
        required_quantity_kg=payload.required_quantity_kg,
        address=address, latitude=lat, longitude=lng,
        urgency=payload.urgency, deadline=payload.deadline,
        pickup_availability=payload.pickup_availability,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _out(r)


@router.get("", response_model=List[RequirementOut])
def list_requirements(mine: bool = False, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    q = db.query(Requirement)
    if mine:
        q = q.filter(Requirement.ngo_id == current_user.id)
    return [_out(r) for r in q.order_by(Requirement.created_at.desc()).all()]


@router.delete("/{requirement_id}")
def delete_requirement(requirement_id: str, db: Session = Depends(get_db),
                       current_user: User = Depends(require_role("ngo", "admin"))):
    r = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if r.ngo_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this requirement")
    db.delete(r)
    db.commit()
    return {"success": True}
