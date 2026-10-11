import os
import sys

os.environ["DATABASE_URL"] = "sqlite://"          # in-memory DB, no MySQL needed for tests
os.environ["GEO_TIMEOUT"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.utils import geo


@pytest.fixture(autouse=True)
def _fresh_db(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def fake_http(url):  # no real network in tests
        if "nominatim" in url or "search" in url:
            return [{"lat": "19.0760", "lon": "72.8777", "display_name": "Mumbai (mock)"}]
        raise OSError("offline")

    monkeypatch.setattr(geo, "_http_json", fake_http)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def register(client, role, name, email, lat=19.07, lng=72.87, **extra):
    body = {"name": name, "email": email, "password": "secret123", "role": role,
            "location": {"address": f"{name} street, Mumbai", "lat": lat, "lng": lng}, **extra}
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    t = client.post("/api/auth/login", json={"email": email, "password": "secret123"}).json()
    return {"Authorization": f"Bearer {t['token']}"}, t["user"]


@pytest.fixture
def users(client):
    donor_h, donor = register(client, "donor", "Hotel Taj", "donor@x.com", 19.0760, 72.8777)
    ngo_h, ngo = register(client, "ngo", "Helping Hands", "ngo@x.com", 19.0900, 72.8800)
    far_h, far = register(client, "ngo", "Far NGO", "far@x.com", 19.3000, 73.1000)
    admin_h, admin = register(client, "admin", "Root", "admin@x.com", admin_code="S2S-ADMIN-2026")
    return dict(donor_h=donor_h, donor=donor, ngo_h=ngo_h, ngo=ngo, far_h=far_h, far=far,
                admin_h=admin_h, admin=admin)


def future(hours):
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def donation_body(food="cooked rice", kg=20, hours=5, **kw):
    return {"food_type": food, "quantity_kg": kg, "servings": kg * 4, "expiry_time": future(hours),
            "storage_condition": "refrigerated",
            "location": {"address": "Taj, Colaba", "lat": 19.0760, "lng": 72.8777}, **kw}


def req_body(food="rice", kg=30, urgency="high", pickup="immediate", **kw):
    return {"food_type": food, "required_quantity_kg": kg, "urgency": urgency,
            "pickup_availability": pickup, **kw}
