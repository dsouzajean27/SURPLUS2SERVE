from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate, RequirementOut
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
def create_requirement(
    payload: RequirementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ngo")),
):
    requirement = Requirement(
        ngo_id=current_user.id,
        food_type=payload.food_type,
        required_quantity_kg=payload.required_quantity_kg,
        address=payload.location.address,
        latitude=payload.location.lat,
        longitude=payload.location.lng,
        urgency=payload.urgency,
        deadline=payload.deadline,
        pickup_availability=payload.pickup_availability,
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


@router.get("", response_model=List[RequirementOut])
def list_requirements(
    mine: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Requirement)
    if mine:
        query = query.filter(Requirement.ngo_id == current_user.id)
    return query.order_by(Requirement.created_at.desc()).all()


@router.delete("/{requirement_id}")
def delete_requirement(
    requirement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ngo", "admin")),
):
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if requirement.ngo_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this requirement")
    db.delete(requirement)
    db.commit()
    return {"success": True}
