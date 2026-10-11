import json
import math
import urllib.parse
import urllib.request
from typing import List, Optional, Tuple

from app.config import settings


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def sort_by_distance(origin_lat, origin_lng, points):
    """points: list of (lat, lng, id) -> list of (id, distance_km) nearest first."""
    result = [(pid, haversine_distance(origin_lat, origin_lng, lat, lng)) for lat, lng, pid in points]
    return sorted(result, key=lambda x: x[1])


def _http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": settings.GEO_USER_AGENT})
    with urllib.request.urlopen(req, timeout=settings.GEO_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode(address: str) -> Optional[Tuple[float, float, str]]:
    """Address -> (lat, lng, display_name) using OpenStreetMap Nominatim.
    Returns None if nothing is found or the service is unreachable."""
    params = urllib.parse.urlencode({"q": address, "format": "json", "limit": 1})
    try:
        data = _http_json(f"{settings.NOMINATIM_URL}?{params}")
    except Exception:
        return None
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", address)


def road_route(lat1: float, lng1: float, lat2: float, lng2: float) -> dict:
    """Driving distance/duration/geometry via the OSRM routing API.
    If OSRM is unreachable, falls back to straight-line distance x 1.3
    (typical road-detour factor) so the app keeps working offline."""
    straight = haversine_distance(lat1, lng1, lat2, lng2)
    url = (
        f"{settings.OSRM_URL}/{lng1},{lat1};{lng2},{lat2}"
        "?overview=simplified&geometries=geojson"
    )
    try:
        data = _http_json(url)
        route = data["routes"][0]
        return {
            "source": "osrm",
            "distance_km": round(route["distance"] / 1000, 2),
            "duration_min": round(route["duration"] / 60, 1),
            "straight_line_km": straight,
            "geometry": [[c[1], c[0]] for c in route["geometry"]["coordinates"]],  # [lat, lng]
        }
    except Exception:
        est = round(straight * 1.3, 2)
        return {
            "source": "estimate",
            "distance_km": est,
            "duration_min": round(est / 25 * 60, 1),  # ~25 km/h city average
            "straight_line_km": straight,
            "geometry": [[lat1, lng1], [lat2, lng2]],
        }


def osm_directions_link(lat1, lng1, lat2, lng2) -> str:
    return (
        "https://www.openstreetmap.org/directions?engine=fossgis_osrm_car"
        f"&route={lat1}%2C{lng1}%3B{lat2}%2C{lng2}"
    )


def nearest_neighbour_order(origin: Tuple[float, float], stops: List[Tuple[float, float, str]]):
    """Greedy nearest-neighbour tour used for multi-donor collection routes."""
    remaining = list(stops)
    order, cur, total = [], origin, 0.0
    while remaining:
        nxt = min(remaining, key=lambda s: haversine_distance(cur[0], cur[1], s[0], s[1]))
        d = haversine_distance(cur[0], cur[1], nxt[0], nxt[1])
        total += d
        order.append((nxt[2], d))
        cur = (nxt[0], nxt[1])
        remaining.remove(nxt)
    return order, round(total, 2)
