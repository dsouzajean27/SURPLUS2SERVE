from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.donation import Donation, DonationStatusHistory
from app.schemas.donation import DonationCreate, DonationOut, StatusUpdate
from app.auth.dependencies import get_current_user, require_role
from app.services.status_flow import is_valid_transition
from app.utils.geo import haversine_km

router = APIRouter(prefix="/api/donations", tags=["donations"])


def _expire_if_past_deadline(donation: Donation, db: Session) -> None:
    """Auto-marks a donation expired if its expiry time has passed and it's
    still in a non-final state. Keeps urgency/status accurate without a
    background job - this check runs on every read."""
    if donation.status not in ("completed", "expired") and donation.expiry_time <= datetime.utcnow():
        donation.status = "expired"
        db.add(DonationStatusHistory(donation_id=donation.id, status="expired", note="Auto-expired"))
        db.commit()
        db.refresh(donation)


@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED)
def create_donation(
    payload: DonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("donor")),
):
    donation = Donation(
        donor_id=current_user.id,
        food_type=payload.food_type,
        quantity_kg=payload.quantity_kg,
        servings=payload.servings,
        prep_time=payload.prep_time,
        expiry_time=payload.expiry_time,
        storage_condition=payload.storage_condition,
        address=payload.location.address,
        latitude=payload.location.lat,
        longitude=payload.location.lng,
        image_url=payload.image_url,
        status="posted",
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)

    db.add(DonationStatusHistory(donation_id=donation.id, status="posted"))
    db.commit()

    return donation


@router.get("", response_model=List[DonationOut])
def list_donations(
    mine: bool = False,
    status_filter: Optional[str] = None,
    near_lat: Optional[float] = None,
    near_lng: Optional[float] = None,
    max_distance_km: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Donation)

    if mine:
        query = query.filter(Donation.donor_id == current_user.id)
    if status_filter:
        query = query.filter(Donation.status == status_filter)

    donations = query.order_by(Donation.created_at.desc()).all()

    for d in donations:
        _expire_if_past_deadline(d, db)

    if near_lat is not None and near_lng is not None:
        annotated = []
        for d in donations:
            dist = haversine_km(near_lat, near_lng, d.latitude, d.longitude)
            if max_distance_km is None or dist <= max_distance_km:
                annotated.append((dist, d))
        annotated.sort(key=lambda pair: pair[0])
        donations = [d for _, d in annotated]

    return donations


@router.get("/{donation_id}", response_model=DonationOut)
def get_donation(
    donation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    _expire_if_past_deadline(donation, db)
    return donation


@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_status(
    donation_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    is_admin = current_user.role == "admin"
    is_owner_donor = current_user.role == "donor" and current_user.id == donation.donor_id
    is_ngo = current_user.role == "ngo"
    if not (is_admin or is_owner_donor or is_ngo):
        raise HTTPException(status_code=403, detail="Not authorized to update this donation")

    if not is_admin and not is_valid_transition(donation.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move donation from '{donation.status}' to '{payload.status}'",
        )

    if payload.status == "accepted":
        if not payload.ngo_id:
            raise HTTPException(status_code=400, detail="ngo_id is required to accept a donation")
        donation.accepted_ngo_id = payload.ngo_id

    donation.status = payload.status
    db.add(DonationStatusHistory(donation_id=donation.id, status=payload.status, note=payload.note))
    db.commit()
    db.refresh(donation)
    return donation
