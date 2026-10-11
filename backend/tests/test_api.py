"""Automated tests - mapped to the report's preliminary test cases TC01-TC14."""
from datetime import datetime, timedelta, timezone

from tests.conftest import register, donation_body, req_body, future


# ---- TC01-TC02, TC12: registration, login, authorisation -------------------
def test_tc01_register_donor(client):
    h, u = register(client, "donor", "A", "a@x.com")
    assert u["role"] == "donor" and u["verified"] is False


def test_register_duplicate_email_rejected(client):
    register(client, "donor", "A", "a@x.com")
    r = client.post("/api/auth/register", json={"name": "B", "email": "A@x.com", "password": "secret123",
                    "role": "donor", "location": {"address": "x", "lat": 1, "lng": 1}})
    assert r.status_code == 409


def test_admin_signup_needs_code(client):
    r = client.post("/api/auth/register", json={"name": "B", "email": "b@x.com", "password": "secret123",
                    "role": "admin", "location": {"address": "x", "lat": 1, "lng": 1}})
    assert r.status_code == 403


def test_tc02_login_valid_and_invalid(client, users):
    ok = client.post("/api/auth/login", json={"email": "donor@x.com", "password": "secret123"})
    assert ok.status_code == 200 and ok.json()["user"]["role"] == "donor"
    bad = client.post("/api/auth/login", json={"email": "donor@x.com", "password": "wrong"})
    assert bad.status_code == 401


def test_address_is_geocoded_when_no_coordinates(client):
    r = client.post("/api/auth/register", json={"name": "G", "email": "g@x.com", "password": "secret123",
                    "role": "donor", "location": {"address": "Colaba, Mumbai"}})
    assert r.status_code == 201 and abs(r.json()["latitude"] - 19.076) < 0.01


def test_tc12_unauthorised_access_denied(client, users):
    assert client.get("/api/donations").status_code in (401, 403)           # no token
    r = client.post("/api/donations", json=donation_body(), headers=users["ngo_h"])
    assert r.status_code == 403                                              # wrong role
    assert client.get("/api/admin/users", headers=users["donor_h"]).status_code == 403


# ---- TC03-TC04: food posting + validation ----------------------------------
def test_tc03_post_valid_donation(client, users):
    r = client.post("/api/donations", json=donation_body(), headers=users["donor_h"])
    assert r.status_code == 201
    d = r.json()
    assert d["status"] == "posted" and d["urgency"] in ("high", "medium", "low") and d["donor_name"] == "Hotel Taj"
    lst = client.get("/api/donations", headers=users["donor_h"]).json()
    assert len(lst) == 1


def test_tc04_invalid_donation_rejected(client, users):
    h = users["donor_h"]
    assert client.post("/api/donations", json=donation_body(kg=-5), headers=h).status_code == 422
    assert client.post("/api/donations", json=donation_body(food=""), headers=h).status_code == 422
    past = donation_body(); past["expiry_time"] = future(-2)
    assert client.post("/api/donations", json=past, headers=h).status_code == 422


# ---- TC05: requirement ------------------------------------------------------
def test_tc05_create_requirement(client, users):
    r = client.post("/api/requirements", json=req_body(), headers=users["ngo_h"])
    assert r.status_code == 201
    assert r.json()["latitude"] == users["ngo"]["latitude"]  # defaulted to profile location
    assert client.post("/api/requirements", json=req_body(), headers=users["donor_h"]).status_code == 403
    assert len(client.get("/api/requirements?mine=true", headers=users["ngo_h"]).json()) == 1


# ---- TC06-TC07: recommendation + distance ----------------------------------
def test_tc06_tc07_recommendation_ranking(client, users):
    client.post("/api/requirements", json=req_body(), headers=users["ngo_h"])
    client.post("/api/requirements", json=req_body(food="rice", kg=30), headers=users["far_h"])
    client.post("/api/requirements", json=req_body(food="laptops", kg=5), headers=users["far_h"])
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()

    rec = client.get(f"/api/recommendations/donation/{d['id']}", headers=users["donor_h"]).json()
    assert rec["fallback"] is None
    ranked = rec["recipients"]
    assert [r["ngo_name"] for r in ranked] == ["Helping Hands", "Far NGO"]    # nearer NGO wins
    assert ranked[0]["distance_km"] < ranked[1]["distance_km"]               # TC07
    assert ranked[0]["score"] > ranked[1]["score"] and ranked[0]["rank"] == 1
    assert all(r["requirement"]["food_type"] != "laptops" for r in ranked)   # incompatible food filtered


def test_recommendation_fallback_when_no_recipient(client, users):
    d = client.post("/api/donations", json=donation_body(food="vegetable peels"), headers=users["donor_h"]).json()
    rec = client.get(f"/api/recommendations/donation/{d['id']}", headers=users["donor_h"]).json()
    assert rec["recipients"] == [] and rec["fallback"]["type"] == "compost"
    assert client.get(f"/api/donations/{d['id']}", headers=users["donor_h"]).json()["fallback_recommendation"] == "compost"


def test_ngo_sees_ranked_open_donations(client, users):
    client.post("/api/requirements", json=req_body(), headers=users["ngo_h"])
    client.post("/api/donations", json=donation_body(), headers=users["donor_h"])
    client.post("/api/donations", json=donation_body(food="tyres"), headers=users["donor_h"])
    r = client.get("/api/recommendations/for-ngo", headers=users["ngo_h"]).json()
    assert len(r) == 1 and r[0]["food_type"] == "cooked rice" and r[0]["match_score"] > 0


# ---- TC08-TC10: accept, track, complete + impact ---------------------------
def test_tc08_tc09_tc10_full_lifecycle(client, users):
    d = client.post("/api/donations", json=donation_body(kg=10), headers=users["donor_h"]).json()
    did = d["id"]
    acc = client.post(f"/api/donations/{did}/accept", headers=users["ngo_h"])
    assert acc.status_code == 200 and acc.json()["status"] == "accepted"                      # TC08
    # second NGO cannot take it
    assert client.post(f"/api/donations/{did}/accept", headers=users["far_h"]).status_code == 409

    patch = lambda s, h: client.patch(f"/api/donations/{did}/status", json={"status": s}, headers=h)
    assert patch("completed", users["ngo_h"]).status_code == 400                              # no skipping
    assert patch("pickup_pending", users["donor_h"]).json()["status"] == "pickup_pending"     # TC09
    assert patch("delivered", users["ngo_h"]).json()["status"] == "delivered"
    assert patch("completed", users["donor_h"]).status_code == 403                            # recipient confirms
    assert patch("completed", users["far_h"]).status_code == 403
    assert patch("completed", users["ngo_h"]).json()["status"] == "completed"                 # TC10

    hist = client.get(f"/api/donations/{did}/history", headers=users["donor_h"]).json()
    assert [h["status"] for h in hist] == ["posted", "accepted", "pickup_pending", "delivered", "completed"]

    imp = client.get("/api/dashboard/impact").json()                                          # TC13
    assert imp["completed_donations"] == 1 and imp["food_rescued_kg"] == 10
    assert imp["servings_redistributed"] == 40 and imp["recipient_orgs_served"] == 1
    assert client.get("/api/dashboard/ngo", headers=users["ngo_h"]).json()["donations_received"] == 1
    assert client.get("/api/dashboard/donor", headers=users["donor_h"]).json()["food_rescued_kg"] == 10


# ---- TC11: expiry -----------------------------------------------------------
def test_tc11_auto_expiry_and_fallback(client, users):
    from app.database import SessionLocal
    from app.models.donation import Donation
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    db = SessionLocal()
    row = db.get(Donation, d["id"])
    row.expiry_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
    db.commit(); db.close()
    got = client.get(f"/api/donations/{d['id']}", headers=users["donor_h"]).json()
    assert got["status"] == "expired" and got["fallback_recommendation"] in ("compost", "animal_feed")
    assert client.get("/api/dashboard/impact").json()["expired_donations"] == 1
    notes = client.get("/api/notifications", headers=users["donor_h"]).json()
    assert any(n["type"] == "expiry_warning" for n in notes)


# ---- FR13: notifications ----------------------------------------------------
def test_notifications_flow(client, users):
    client.post("/api/requirements", json=req_body(), headers=users["ngo_h"])
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    ngo_notes = client.get("/api/notifications", headers=users["ngo_h"]).json()
    assert any(n["type"] == "new_match" for n in ngo_notes)
    client.post(f"/api/donations/{d['id']}/accept", headers=users["ngo_h"])
    donor_notes = client.get("/api/notifications", headers=users["donor_h"]).json()
    assert any(n["type"] == "accepted" for n in donor_notes)
    assert client.get("/api/notifications/unread-count", headers=users["donor_h"]).json()["unread"] >= 1
    nid = donor_notes[0]["id"]
    assert client.patch(f"/api/notifications/{nid}/read", headers=users["donor_h"]).status_code == 200
    assert client.patch(f"/api/notifications/{nid}/read", headers=users["ngo_h"]).status_code == 404  # not theirs
    client.patch("/api/notifications/read-all", headers=users["donor_h"])
    assert client.get("/api/notifications/unread-count", headers=users["donor_h"]).json()["unread"] == 0


def test_expiry_warning_for_urgent_donation(client, users):
    client.post("/api/donations", json=donation_body(hours=2), headers=users["donor_h"])
    notes = client.get("/api/notifications", headers=users["donor_h"]).json()
    assert any(n["type"] == "expiry_warning" for n in notes)


# ---- visibility / privacy ---------------------------------------------------
def test_visibility_rules(client, users):
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    _, other = register(client, "donor", "Other", "other@x.com")
    other_h = {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": "other@x.com", "password": "secret123"}).json()["token"]}
    assert client.get("/api/donations", headers=other_h).json() == []
    assert client.get(f"/api/donations/{d['id']}", headers=other_h).status_code == 403
    assert len(client.get("/api/donations", headers=users["ngo_h"]).json()) == 1   # open donation visible
    client.post(f"/api/donations/{d['id']}/accept", headers=users["ngo_h"])
    assert client.get(f"/api/donations/{d['id']}", headers=users["far_h"]).status_code == 403
    assert len(client.get("/api/donations", headers=users["admin_h"]).json()) == 1


def test_edit_and_delete_rules(client, users):
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    r = client.put(f"/api/donations/{d['id']}", json={"quantity_kg": 99}, headers=users["donor_h"])
    assert r.status_code == 200 and r.json()["quantity_kg"] == 99
    client.post(f"/api/donations/{d['id']}/accept", headers=users["ngo_h"])
    assert client.put(f"/api/donations/{d['id']}", json={"quantity_kg": 1}, headers=users["donor_h"]).status_code == 400
    assert client.delete(f"/api/donations/{d['id']}", headers=users["donor_h"]).status_code == 400
    assert client.delete(f"/api/donations/{d['id']}", headers=users["admin_h"]).status_code == 200


# ---- FR11: routes -----------------------------------------------------------
def test_route_and_collection(client, users):
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    assert client.get(f"/api/routes/donation/{d['id']}", headers=users["donor_h"]).status_code == 400  # not accepted yet
    client.post(f"/api/donations/{d['id']}/accept", headers=users["ngo_h"])
    r = client.get(f"/api/routes/donation/{d['id']}", headers=users["donor_h"]).json()
    assert r["source"] == "estimate" and r["distance_km"] > 0 and r["directions_url"].startswith("https://www.openstreetmap.org")
    col = client.get("/api/routes/collection", headers=users["ngo_h"]).json()
    assert len(col["stops"]) == 1
    assert client.get(f"/api/routes/donation/{d['id']}", headers=users["far_h"]).status_code == 403


# ---- FR16: demand -----------------------------------------------------------
def test_demand_forecast(client, users):
    r = client.post("/api/demand/predict", json={"history": [[1, 50], [2, 60], [3, 70]]}, headers=users["ngo_h"])
    assert r.status_code == 200 and r.json()["forecast"][0] == 80.0 and len(r.json()["forecast"]) == 7
    client.post("/api/requirements", json=req_body(), headers=users["ngo_h"])
    f = client.get("/api/demand/forecast", headers=users["ngo_h"]).json()
    assert len(f["forecast"]) == 7 and "rice" in f["food_types"]


# ---- FR15: admin ------------------------------------------------------------
def test_admin_overview_and_verify(client, users):
    client.post("/api/donations", json=donation_body(), headers=users["donor_h"])
    ov = client.get("/api/admin/overview", headers=users["admin_h"]).json()
    assert ov["users_by_role"]["ngo"] == 2 and ov["donations_by_status"]["posted"] == 1
    assert ov["unverified_users"] == 3 and len(ov["recent_activity"]) >= 1
    r = client.patch(f"/api/admin/users/{users['ngo']['id']}/verify", headers=users["admin_h"])
    assert r.json()["verified"] is True


# ---- TC14: bad API request --------------------------------------------------
def test_tc14_invalid_requests(client, users):
    assert client.post("/api/auth/login", json={"email": "not-an-email", "password": "x"}).status_code == 422
    assert client.get("/api/donations/does-not-exist", headers=users["donor_h"]).status_code == 404
    assert client.get("/api/donations", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_urgency_rules():
    from app.services.urgency import classify_urgency
    now = datetime(2026, 1, 1, 12, 0)
    assert classify_urgency(now + timedelta(hours=3), now=now)["level"] == "high"
    assert classify_urgency(now + timedelta(hours=12), now=now)["level"] == "medium"
    assert classify_urgency(now + timedelta(days=3), now=now)["level"] == "low"
    # cooked food left at room temp for 3h is high urgency even if label expiry is far away
    assert classify_urgency(now + timedelta(days=3), prep_time=now - timedelta(hours=3), now=now)["level"] == "high"
