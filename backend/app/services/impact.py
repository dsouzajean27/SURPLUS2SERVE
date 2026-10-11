"""Impact & analytics (FR14)."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.donation import Donation
from app.models.user import User

# Rough, commonly cited estimate: wasted food ~2.5 kg CO2e per kg. Shown as an *estimate*.
CO2E_PER_KG = 2.5


def impact_summary(db: Session, donor_id=None, ngo_id=None) -> dict:
    q = db.query(Donation)
    if donor_id:
        q = q.filter(Donation.donor_id == donor_id)
    if ngo_id:
        q = q.filter(Donation.accepted_ngo_id == ngo_id)
    rows = q.all()
    completed = [d for d in rows if d.status == "completed"]
    kg = round(sum(d.quantity_kg for d in completed), 2)
    total = len(rows)
    return {
        "total_donations": total,
        "completed_donations": len(completed),
        "expired_donations": sum(d.status == "expired" for d in rows),
        "active_donations": sum(d.status in ("posted", "accepted", "pickup_pending", "delivered") for d in rows),
        "food_rescued_kg": kg,
        "servings_redistributed": round(sum(d.servings for d in completed)),
        "recipient_orgs_served": len({d.accepted_ngo_id for d in completed if d.accepted_ngo_id}),
        "donors_participating": len({d.donor_id for d in rows}),
        "waste_avoided_kg": kg,
        "co2e_avoided_kg_estimate": round(kg * CO2E_PER_KG, 1),
        "completion_rate": round(len(completed) / total * 100, 1) if total else 0,
    }
