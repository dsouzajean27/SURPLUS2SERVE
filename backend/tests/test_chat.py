from tests.conftest import donation_body, register


def _accepted(client, users):
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    assert client.post(f"/api/donations/{d['id']}/accept", headers=users["ngo_h"]).status_code == 200
    return d["id"]


def test_contact_and_chat_flow(client, users):
    did = _accepted(client, users)
    c = client.get(f"/api/donations/{did}/contact", headers=users["donor_h"]).json()
    assert c["donor"]["name"] == "Hotel Taj" and c["ngo"]["name"] == "Helping Hands"
    r = client.post(f"/api/donations/{did}/messages", json={"text": "Pickup at 6pm?"}, headers=users["ngo_h"])
    assert r.status_code == 201
    client.post(f"/api/donations/{did}/messages", json={"text": "Yes, see you"}, headers=users["donor_h"])
    msgs = client.get(f"/api/donations/{did}/messages", headers=users["donor_h"]).json()
    assert [m["text"] for m in msgs] == ["Pickup at 6pm?", "Yes, see you"]
    assert [m["mine"] for m in msgs] == [False, True]
    notes = client.get("/api/notifications", headers=users["donor_h"]).json()
    assert any("Pickup at 6pm" in n["message"] for n in notes)


def test_chat_blocked_before_accept_and_for_outsiders(client, users):
    d = client.post("/api/donations", json=donation_body(), headers=users["donor_h"]).json()
    assert client.get(f"/api/donations/{d['id']}/contact", headers=users["donor_h"]).status_code == 400
    did = _accepted(client, users)
    assert client.get(f"/api/donations/{did}/messages", headers=users["far_h"]).status_code == 403
    assert client.post(f"/api/donations/{did}/messages", json={"text": "hi"}, headers=users["far_h"]).status_code == 403
    assert client.post(f"/api/donations/{did}/messages", json={"text": "hi"}, headers=users["admin_h"]).status_code == 403
    assert client.get(f"/api/donations/{did}/messages", headers=users["admin_h"]).status_code == 200
    assert client.post(f"/api/donations/{did}/messages", json={"text": "   "}, headers=users["ngo_h"]).status_code == 422
