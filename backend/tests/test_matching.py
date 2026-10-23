from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.services.recommender import food_category, rank_recipients
from tests.conftest import donation_body, req_body


def _req(ngo_id, food, lat=19.09, lng=72.88, kg=30):
    return SimpleNamespace(id=f"r-{ngo_id}", ngo_id=ngo_id, ngo=SimpleNamespace(name=ngo_id), food_type=food,
                           required_quantity_kg=kg, latitude=lat, longitude=lng, address="x",
                           urgency="medium", pickup_availability="immediate", deadline=None)


def _don(food="roti", hours=5, lat=19.076, lng=72.877):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return SimpleNamespace(food_type=food, quantity_kg=10, latitude=lat, longitude=lng,
                           expiry_time=now + timedelta(hours=hours), prep_time=None, storage_condition="refrigerated")


def test_category_knowledge():
    assert food_category("fresh roti") == "bread" == food_category("chapati")
    assert food_category("chicken biryani") == "cooked_meal"
    assert food_category("xyz") is None


def test_roti_matches_chapati_need_but_not_milk():
    ranked = rank_recipients(_don("roti"), [_req("A", "chapati"), _req("B", "milk")])
    assert [r["ngo_id"] for r in ranked] == ["A"]


def test_unreachable_ngo_is_excluded():
    # food has ~1 h left, NGO is ~100 km away (needs ~5 h at 20 km/h)
    ranked = rank_recipients(_don("roti", hours=1), [_req("near", "roti"), _req("far", "roti", lat=20.0, lng=73.8)])
    assert [r["ngo_id"] for r in ranked] == ["near"]


def test_reliability_changes_ranking():
    reqs = [_req("good", "roti"), _req("bad", "roti")]
    ranked = rank_recipients(_don(), reqs, reliability={"good": 0.9, "bad": 0.2})
    assert ranked[0]["ngo_id"] == "good"
    assert ranked[0]["breakdown"]["reliability"] > ranked[1]["breakdown"]["reliability"]


def test_reliability_learned_from_history_via_api(client, users):
    from app.database import SessionLocal
    from app.services.donations import ngo_reliability_map
    h, ngo = users["donor_h"], users["ngo_h"]
    for _ in range(2):
        d = client.post("/api/donations", json=donation_body(), headers=h).json()
        client.post(f"/api/donations/{d['id']}/accept", headers=ngo)
        client.patch(f"/api/donations/{d['id']}/status", json={"status": "pickup_pending"}, headers=ngo)
        client.patch(f"/api/donations/{d['id']}/status", json={"status": "delivered"}, headers=ngo)
    db = SessionLocal()
    try:
        m = ngo_reliability_map(db)
    finally:
        db.close()
    assert m[users["ngo"]["id"]] > 0.5
