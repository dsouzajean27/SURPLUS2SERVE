from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.donation import Donation
from app.models.user import User
from app.utils.geo import road_route, osm_directions_link, nearest_neighbour_order

router = APIRouter(prefix="/api/routes", tags=["routes"])


@router.get("/donation/{donation_id}")
def donation_route(donation_id: str, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    """FR11 - pickup route from the donor to the recipient (accepted NGO)."""
    d = db.query(Donation).filter(Donation.id == donation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    if not d.accepted_ngo:
        raise HTTPException(status_code=400, detail="Route is available once an NGO has accepted the donation")
    ngo = d.accepted_ngo
    if current_user.role == "donor" and d.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your donation")
    if current_user.role == "ngo" and ngo.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your pickup")
    if ngo.latitude is None:
        raise HTTPException(status_code=400, detail="Recipient has no location on file")
    route = road_route(d.latitude, d.longitude, ngo.latitude, ngo.longitude)
    route.update({
        "from": {"name": d.donor.name if d.donor else "Donor", "address": d.address, "lat": d.latitude, "lng": d.longitude},
        "to": {"name": ngo.name, "address": ngo.address, "lat": ngo.latitude, "lng": ngo.longitude},
        "directions_url": osm_directions_link(d.latitude, d.longitude, ngo.latitude, ngo.longitude),
    })
    return route


@router.get("/collection")
def collection_route(db: Session = Depends(get_db), current_user: User = Depends(require_role("ngo"))):
    """Extended feature: one trip that collects from several donors.
    Orders this NGO's pending pickups with a nearest-neighbour tour starting at the NGO."""
    pending = db.query(Donation).filter(Donation.accepted_ngo_id == current_user.id,
                                        Donation.status.in_(["accepted", "pickup_pending"])).all()
    if not pending:
        return {"stops": [], "total_km": 0, "message": "No pickups waiting"}
    by_id = {d.id: d for d in pending}
    order, total = nearest_neighbour_order(
        (current_user.latitude, current_user.longitude),
        [(d.latitude, d.longitude, d.id) for d in pending])
    stops = [{"order": i, "donation_id": did, "donor_name": by_id[did].donor.name,
              "food_type": by_id[did].food_type, "address": by_id[did].address,
              "lat": by_id[did].latitude, "lng": by_id[did].longitude, "leg_km": leg}
             for i, (did, leg) in enumerate(order, 1)]
    return {"start": {"lat": current_user.latitude, "lng": current_user.longitude, "name": current_user.name},
            "stops": stops, "total_km": total}
