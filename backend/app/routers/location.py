from fastapi import APIRouter, HTTPException, Query

from app.utils.geo import geocode

router = APIRouter(prefix="/api/location", tags=["location"])


@router.get("/geocode")
def geocode_address(q: str = Query(min_length=3)):
    """Address -> coordinates (OpenStreetMap Nominatim). Used by the 'Find on map' buttons."""
    found = geocode(q)
    if not found:
        raise HTTPException(status_code=404, detail="Address not found (or the geocoding service is unreachable)")
    lat, lng, display = found
    return {"lat": lat, "lng": lng, "display_name": display}
