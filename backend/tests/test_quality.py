"""Phase 5 - food quality verification."""
from datetime import datetime, timedelta, timezone

from app.services.quality import assess_quality, check_temperature
from tests.conftest import donation_body

GOOD = dict(hygienic_prep=True, not_plate_leftovers=True, stored_properly=True,
            clean_container=True, no_spoilage_signs=True)


def hours_ago(h):
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()


def safe_body(**kw):
    base = dict(prep_time=hours_ago(1), packaging="sealed", hygiene_checklist=GOOD,
                image_url="https://example.com/x.jpg")
    base.update(kw)
    return donation_body(**base)


# ---- the rule engine ------------------------------------------------------
def _assess(**kw):
    now = datetime(2026, 1, 1, 12, 0)
    args = dict(food_type="cooked rice", storage_condition="refrigerated",
                prep_time=now - timedelta(hours=1), expiry_time=now + timedelta(hours=6),
                packaging="sealed", checklist=GOOD, has_photo=True, now=now)
    args.update(kw)
    return assess_quality(**args)


def test_clean_donation_scores_good():
    q = _assess()
    assert q["score"] == 100 and q["status"] == "good" and not q["blockers"]


def test_room_temp_cooked_food_past_4h_is_rejected():
    q = _assess(storage_condition="room_temp", prep_time=datetime(2026, 1, 1, 6, 0))
    assert q["status"] == "rejected" and "safe window" in q["blockers"][0]


def test_raw_vegetables_get_longer_room_temp_window():
    q = _assess(food_type="raw carrots", storage_condition="room_temp", prep_time=datetime(2026, 1, 1, 6, 0))
    assert q["status"] != "rejected"


def test_plate_leftovers_and_spoilage_are_blockers():
    assert _assess(checklist={**GOOD, "not_plate_leftovers": False})["status"] == "rejected"
    assert _assess(checklist={**GOOD, "no_spoilage_signs": False})["status"] == "rejected"


def test_missing_checklist_is_caution_not_rejected():
    q = _assess(checklist=None, has_photo=False)
    assert q["status"] == "caution" and any("checklist" in n for n in q["notes"])


def test_score_drops_as_food_ages():
    young = _assess(prep_time=datetime(2026, 1, 1, 11, 0))["score"]
    old = _assess(prep_time=datetime(2026, 1, 1, 12, 0) - timedelta(hours=40))["score"]
    assert old < young


def test_temperature_rule():
    assert check_temperature("refrigerated", 4) is None
    assert check_temperature("refrigerated", 12) is not None
    assert check_temperature("frozen", -5) is not None
    assert check_temperature("room_temp", 30) is None


# ---- API ------------------------------------------------------------------
def test_unsafe_food_cannot_be_posted(client, users):
    r = client.post("/api/donations", json=safe_body(
        hygiene_checklist={**GOOD, "not_plate_leftovers": False}), headers=users["donor_h"])
    assert r.status_code == 422 and "safety check" in r.json()["detail"]
    r = client.post("/api/donations", json=donation_body(
        prep_time=hours_ago(10), storage_condition="room_temp"), headers=users["donor_h"])
    assert r.status_code == 422


def test_safe_food_is_posted_with_quality_info(client, users):
    r = client.post("/api/donations", json=safe_body(allergens="nuts"), headers=users["donor_h"])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["quality"]["status"] == "good" and d["allergens"] == "nuts" and d["packaging"] == "sealed"
    assert d["hygiene_checklist"]["hygienic_prep"] is True and d["inspection"] is None


def test_quality_preview(client, users):
    body = {"food_type": "cooked rice", "storage_condition": "refrigerated",
            "expiry_time": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
            "hygiene_checklist": GOOD, "packaging": "sealed", "has_photo": True}
    r = client.post("/api/donations/quality-preview", json=body, headers=users["donor_h"])
    assert r.status_code == 200 and r.json()["status"] == "good"
    assert client.post("/api/donations/quality-preview", json=body, headers=users["ngo_h"]).status_code == 403


def test_inspection_pass_flow(client, users):
    did = client.post("/api/donations", json=safe_body(), headers=users["donor_h"]).json()["id"]
    url = f"/api/donations/{did}/inspection"
    # must be accepted first, by the right NGO
    assert client.post(url, json={"result": "passed"}, headers=users["ngo_h"]).status_code == 403
    client.post(f"/api/donations/{did}/accept", headers=users["ngo_h"])
    assert client.post(url, json={"result": "passed"}, headers=users["far_h"]).status_code == 403
    assert client.post(url, json={"result": "passed"}, headers=users["donor_h"]).status_code == 403
    r = client.post(url, json={"result": "passed", "temperature_c": 3.5}, headers=users["ngo_h"])
    assert r.status_code == 200 and r.json()["inspection"]["result"] == "passed"
    for s in ("pickup_pending", "delivered", "completed"):
        assert client.patch(f"/api/donations/{did}/status", json={"status": s},
                            headers=users["ngo_h"]).status_code == 200


def test_warm_fridge_food_cannot_pass(client, users):
    did = client.post("/api/donations", json=safe_body(), headers=users["donor_h"]).json()["id"]
    client.post(f"/api/donations/{did}/accept", headers=users["ngo_h"])
    r = client.post(f"/api/donations/{did}/inspection", json={"result": "passed", "temperature_c": 14},
                    headers=users["ngo_h"])
    assert r.status_code == 422 and "limit" in r.json()["detail"]


def test_failed_inspection_blocks_delivery_and_notifies(client, users):
    did = client.post("/api/donations", json=safe_body(), headers=users["donor_h"]).json()["id"]
    client.post(f"/api/donations/{did}/accept", headers=users["ngo_h"])
    url = f"/api/donations/{did}/inspection"
    assert client.post(url, json={"result": "failed"}, headers=users["ngo_h"]).status_code == 422  # reason needed
    r = client.post(url, json={"result": "failed", "notes": "sour smell"}, headers=users["ngo_h"])
    assert r.status_code == 200 and r.json()["fallback_recommendation"] != "none"
    client.patch(f"/api/donations/{did}/status", json={"status": "pickup_pending"}, headers=users["ngo_h"])
    r = client.patch(f"/api/donations/{did}/status", json={"status": "delivered"}, headers=users["ngo_h"])
    assert r.status_code == 409
    notes = client.get("/api/notifications", headers=users["donor_h"]).json()
    assert any("FAILED" in n["message"] for n in notes)
    # donor can still write it off -> recovery route
    assert client.patch(f"/api/donations/{did}/status", json={"status": "expired"},
                        headers=users["donor_h"]).status_code == 200
