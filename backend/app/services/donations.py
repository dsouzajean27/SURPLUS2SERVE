"""Shared donation logic: serialisation, auto-expiry, matching notifications."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.donation import Donation, DonationStatusHistory
from app.models.notification import Notification
from app.models.requirement import Requirement
from app.services.notifications import create_notification, notify_status_change
from app.services.recommender import rank_recipients
from app.services.status_flow import EXPIRABLE
from app.services.urgency import classify_urgency, fallback_use, FALLBACK_TEXT, HIGH_HOURS
from app.utils.geo import haversine_distance
from app.utils.timeutil import utcnow


def serialize_donation(d: Donation, origin: Optional[tuple] = None) -> dict:
    u = classify_urgency(d.expiry_time, d.prep_time, d.storage_condition)
    return {
        "id": d.id, "donor_id": d.donor_id,
        "donor_name": d.donor.name if d.donor else None,
        "food_type": d.food_type, "quantity_kg": d.quantity_kg, "servings": d.servings,
        "prep_time": d.prep_time, "expiry_time": d.expiry_time,
        "storage_condition": d.storage_condition or "room_temp",
        "address": d.address, "latitude": d.latitude, "longitude": d.longitude,
        "image_url": d.image_url, "status": d.status,
        "fallback_recommendation": d.fallback_recommendation or "none",
        "accepted_ngo_id": d.accepted_ngo_id,
        "accepted_ngo_name": d.accepted_ngo.name if d.accepted_ngo else None,
        "created_at": d.created_at,
        "urgency": u["level"], "hours_left": u["hours_left"], "urgency_reason": u["reason"],
        "distance_km": haversine_distance(origin[0], origin[1], d.latitude, d.longitude) if origin else None,
    }


def add_history(db: Session, donation_id: str, status: str, note: Optional[str] = None) -> None:
    db.add(DonationStatusHistory(donation_id=donation_id, status=status, note=note))


def expire_if_needed(d: Donation, db: Session) -> bool:
    """Auto-expires a donation whose expiry time has passed (checked on every read,
    so no background job is needed). Returns True if it changed."""
    if d.status in EXPIRABLE and d.expiry_time <= utcnow():
        was_unaccepted = d.status == "posted"
        d.status = "expired"
        if was_unaccepted or not d.fallback_recommendation or d.fallback_recommendation == "none":
            d.fallback_recommendation = fallback_use(d.food_type)
        add_history(db, d.id, "expired", "Auto-expired: expiry time passed. "
                    + FALLBACK_TEXT.get(d.fallback_recommendation, ""))
        db.commit()
        db.refresh(d)
        notify_status_change(db, d, "expired", actor_id="")
        return True
    return False


def notify_matching_ngos(db: Session, donation: Donation) -> list:
    """After a donation is posted: rank recipients, notify the top matches, and if
    nobody is suitable store the circular-economy fallback (FR12)."""
    reqs = db.query(Requirement).all()
    ranked = rank_recipients(donation, reqs, top_k=5)
    if not ranked:
        donation.fallback_recommendation = fallback_use(donation.food_type)
        create_notification(db, donation.donor_id, FALLBACK_TEXT[donation.fallback_recommendation],
                            "info", donation.id, commit=False)
        db.commit()
        return []
    for r in ranked:
        create_notification(
            db, r["ngo_id"],
            f"New donation matches your need: {donation.food_type} ({donation.quantity_kg:g} kg), "
            f"{r['distance_km']:.1f} km away - match {r['score']:.0f}%.",
            "new_match", donation.id, commit=False)
    db.commit()
    return ranked


def scan_expiry_warnings(db: Session, user) -> None:
    """Creates a one-time 'approaching expiry' notification for the user's active donations."""
    q = db.query(Donation).filter(Donation.status.in_(list(EXPIRABLE)))
    if user.role == "donor":
        q = q.filter(Donation.donor_id == user.id)
    elif user.role == "ngo":
        q = q.filter(Donation.accepted_ngo_id == user.id)
    else:
        return
    for d in q.all():
        u = classify_urgency(d.expiry_time, d.prep_time, d.storage_condition)
        if 0 < u["hours_left"] <= HIGH_HOURS:
            exists = db.query(Notification).filter(
                Notification.user_id == user.id, Notification.related_donation_id == d.id,
                Notification.type == "expiry_warning").first()
            if not exists:
                create_notification(db, user.id,
                                    f"Urgent: '{d.food_type}' expires in about {u['hours_left']:.1f} h.",
                                    "expiry_warning", d.id)
