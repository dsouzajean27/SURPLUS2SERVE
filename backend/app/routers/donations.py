from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.donation import Donation, DonationStatusHistory
from app.schemas.donation import DonationCreate, DonationOut, DonationUpdate, StatusUpdate, HistoryOut
from app.auth.dependencies import get_current_user, require_role
from app.services.status_flow import is_valid_transition, EXPIRABLE
from app.services.donations import (serialize_donation, add_history, expire_if_needed,
                                    notify_matching_ngos)
from app.services.notifications import notify_status_change
from app.services.location import resolve_location
from app.utils.timeutil import utcnow

router = APIRouter(prefix="/api/donations", tags=["donations"])


def _expire_overdue(db: Session) -> None:
    overdue = db.query(Donation).filter(Donation.status.in_(list(EXPIRABLE)),
                                        Donation.expiry_time <= utcnow()).all()
    for d in overdue:
        expire_if_needed(d, db)


def _get_or_404(db: Session, donation_id: str) -> Donation:
    d = db.query(Donation).filter(Donation.id == donation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    expire_if_needed(d, db)
    return d


def _check_view(user: User, d: Donation) -> None:
    if user.role == "admin":
        return
    if user.role == "donor" and d.donor_id == user.id:
        return
    if user.role == "ngo" and (d.status == "posted" or d.accepted_ngo_id == user.id):
        return
    raise HTTPException(status_code=403, detail="You do not have access to this donation")


def _accept(db: Session, d: Donation, ngo: User, note: Optional[str]) -> None:
    d.accepted_ngo_id = ngo.id
    d.status = "accepted"
    d.fallback_recommendation = "none"
    add_history(db, d.id, "accepted", note or f"Accepted by {ngo.name}")
    db.commit()
    db.refresh(d)
    notify_status_change(db, d, "accepted", actor_id=ngo.id)


@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED)
def create_donation(payload: DonationCreate, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("donor"))):
    if payload.expiry_time <= utcnow():
        raise HTTPException(status_code=422, detail="expiry_time must be in the future")
    address, lat, lng = resolve_location(payload.location)
    donation = Donation(
        donor_id=current_user.id, food_type=payload.food_type.strip(),
        quantity_kg=payload.quantity_kg, servings=payload.servings,
        prep_time=payload.prep_time, expiry_time=payload.expiry_time,
        storage_condition=payload.storage_condition,
        address=address, latitude=lat, longitude=lng,
        image_url=payload.image_url, status="posted",
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)
    add_history(db, donation.id, "posted", "Donation posted")
    db.commit()
    notify_matching_ngos(db, donation)
    db.refresh(donation)
    return serialize_donation(donation)


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
    """Donors see their own donations, NGOs see open donations + the ones they accepted,
    admins see everything."""
    _expire_overdue(db)
    q = db.query(Donation)
    if current_user.role == "donor":
        q = q.filter(Donation.donor_id == current_user.id)
    elif current_user.role == "ngo":
        if mine:
            q = q.filter(Donation.accepted_ngo_id == current_user.id)
        else:
            q = q.filter((Donation.status == "posted") | (Donation.accepted_ngo_id == current_user.id))
    elif mine:
        q = q.filter(Donation.donor_id == current_user.id)
    if status_filter:
        q = q.filter(Donation.status == status_filter)
    donations = q.order_by(Donation.created_at.desc()).all()

    origin = None
    if near_lat is not None and near_lng is not None:
        origin = (near_lat, near_lng)
    elif current_user.role == "ngo" and current_user.latitude is not None:
        origin = (current_user.latitude, current_user.longitude)

    rows = [serialize_donation(d, origin) for d in donations]
    if max_distance_km is not None and origin:
        rows = [r for r in rows if r["distance_km"] <= max_distance_km]
    if near_lat is not None and near_lng is not None:
        rows.sort(key=lambda r: r["distance_km"])
    return rows


@router.get("/{donation_id}", response_model=DonationOut)
def get_donation(donation_id: str, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    d = _get_or_404(db, donation_id)
    _check_view(current_user, d)
    origin = (current_user.latitude, current_user.longitude) if current_user.role == "ngo" and current_user.latitude is not None else None
    return serialize_donation(d, origin)


@router.get("/{donation_id}/history", response_model=List[HistoryOut])
def donation_history(donation_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    d = _get_or_404(db, donation_id)
    _check_view(current_user, d)
    return (db.query(DonationStatusHistory).filter(DonationStatusHistory.donation_id == d.id)
            .order_by(DonationStatusHistory.changed_at.asc()).all())


@router.put("/{donation_id}", response_model=DonationOut)
def edit_donation(donation_id: str, payload: DonationUpdate, db: Session = Depends(get_db),
                  current_user: User = Depends(require_role("donor"))):
    d = _get_or_404(db, donation_id)
    if d.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your donation")
    if d.status != "posted":
        raise HTTPException(status_code=400, detail="Only donations that are still 'posted' can be edited")
    data = payload.model_dump(exclude_unset=True, exclude={"location"})
    for k, v in data.items():
        if v is not None:
            setattr(d, k, v)
    if payload.location:
        d.address, d.latitude, d.longitude = resolve_location(payload.location)
    if d.prep_time and d.prep_time >= d.expiry_time:
        raise HTTPException(status_code=422, detail="expiry_time must be after prep_time")
    db.commit()
    db.refresh(d)
    return serialize_donation(d)


@router.delete("/{donation_id}")
def delete_donation(donation_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("donor", "admin"))):
    d = _get_or_404(db, donation_id)
    if current_user.role == "donor" and d.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your donation")
    if current_user.role == "donor" and d.status != "posted":
        raise HTTPException(status_code=400, detail="Only donations that are still 'posted' can be removed")
    db.delete(d)
    db.commit()
    return {"success": True}


@router.post("/{donation_id}/accept", response_model=DonationOut)
def accept_donation(donation_id: str, db: Session = Depends(get_db),
                    current_user: User = Depends(require_role("ngo"))):
    """FR09 - an NGO accepts an available donation."""
    d = _get_or_404(db, donation_id)
    if d.status != "posted":
        raise HTTPException(status_code=409, detail=f"Donation is no longer available (status: {d.status})")
    _accept(db, d, current_user, None)
    return serialize_donation(d, (current_user.latitude, current_user.longitude))


@router.patch("/{donation_id}/status", response_model=DonationOut)
def update_status(donation_id: str, payload: StatusUpdate, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    d = _get_or_404(db, donation_id)
    is_admin = current_user.role == "admin"
    is_owner = current_user.role == "donor" and current_user.id == d.donor_id
    is_recipient = current_user.role == "ngo" and current_user.id == d.accepted_ngo_id
    new = payload.status

    if not is_valid_transition(d.status, new):
        raise HTTPException(status_code=400, detail=f"Cannot move donation from '{d.status}' to '{new}'")

    if new == "accepted":
        if current_user.role == "ngo":
            ngo = current_user
        elif is_admin and payload.ngo_id:
            ngo = db.get(User, payload.ngo_id)
            if not ngo or ngo.role != "ngo":
                raise HTTPException(status_code=400, detail="ngo_id must be an NGO user")
        else:
            raise HTTPException(status_code=403, detail="Only an NGO (or an admin naming ngo_id) can accept")
        _accept(db, d, ngo, payload.note)
        return serialize_donation(d)

    allowed = {
        "pickup_pending": is_admin or is_owner or is_recipient,
        "delivered": is_admin or is_owner or is_recipient,
        "completed": is_admin or is_recipient,  # the recipient confirms receipt
        "expired": is_admin or is_owner,
    }.get(new, False)
    if not allowed:
        raise HTTPException(status_code=403, detail="You are not allowed to make this status change")

    d.status = new
    add_history(db, d.id, new, payload.note)
    db.commit()
    db.refresh(d)
    notify_status_change(db, d, new, actor_id=current_user.id)
    return serialize_donation(d)
