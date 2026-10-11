from fastapi import HTTPException

from app.schemas.common import LocationIn
from app.utils.geo import geocode


def resolve_location(loc: LocationIn):
    """Returns (address, lat, lng). Geocodes the address if lat/lng weren't supplied."""
    if loc.lat is not None and loc.lng is not None:
        return loc.address.strip(), loc.lat, loc.lng
    found = geocode(loc.address)
    if not found:
        raise HTTPException(
            status_code=422,
            detail="Could not find that address. Try a more specific address, "
            "or use 'Use my location' / click the map to pick the spot.",
        )
    lat, lng, _ = found
    return loc.address.strip(), lat, lng
