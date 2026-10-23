from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.donation import Donation
from app.models.requirement import Requirement
from app.models.user import User
from app.services.donations import expire_if_needed, serialize_donation, ngo_reliability_map
from app.services.recommender import rank_recipients, rank_donations_for_ngo
from app.services.urgency import fallback_use, FALLBACK_TEXT

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/donation/{donation_id}")
def recommend_for_donation(donation_id: str, db: Session = Depends(get_db),
                           current_user: User = Depends(require_role("donor", "admin"))):
    """Ranked list of suitable recipient organisations for a donation (FR06).
    If nobody is suitable, returns the circular-economy fallback (FR12)."""
    d = db.query(Donation).filter(Donation.id == donation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    if current_user.role == "donor" and d.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your donation")
    expire_if_needed(d, db)

    ranked = rank_recipients(d, db.query(Requirement).all(), top_k=5, reliability=ngo_reliability_map(db))
    fallback = None
    if not ranked and d.status in ("posted", "expired"):
        kind = d.fallback_recommendation if d.fallback_recommendation != "none" else fallback_use(d.food_type)
        if d.fallback_recommendation != kind:
            d.fallback_recommendation = kind
            db.commit()
        fallback = {"type": kind, "message": FALLBACK_TEXT[kind]}
    return {"donation_id": d.id, "recommended": ranked[0] if ranked else None,
            "recipients": ranked, "fallback": fallback}


@router.get("/for-ngo")
def recommend_for_ngo(radius_km: Optional[float] = None, db: Session = Depends(get_db),
                      current_user: User = Depends(require_role("ngo"))):
    """Open donations ranked by how well they fit *this* NGO's current requirements."""
    reqs = db.query(Requirement).filter(Requirement.ngo_id == current_user.id).all()
    open_donations = db.query(Donation).filter(Donation.status == "posted").all()
    for d in open_donations:
        expire_if_needed(d, db)
    open_donations = [d for d in open_donations if d.status == "posted"]
    ranked = rank_donations_for_ngo(open_donations, reqs, reliability=ngo_reliability_map(db))
    origin = (current_user.latitude, current_user.longitude) if current_user.latitude is not None else None
    out = []
    for r in ranked:
        item = serialize_donation(r["donation"], origin)
        if radius_km is not None and origin and item["distance_km"] > radius_km:
            continue  # outside the NGO's chosen radius
        item.update({"match_score": r["score"], "match_breakdown": r["breakdown"],
                     "match_explanation": r["explanation"]})
        out.append(item)
    return out
