"""Fills the database with demo data for the presentation.

    cd backend
    python seed_demo.py          # adds demo users/requirements/donations (safe to re-run)
    python seed_demo.py --reset  # wipes ALL tables first

Demo logins (password for all: demo1234)
    admin@s2s.com   donor1@s2s.com   donor2@s2s.com   ngo1@s2s.com   ngo2@s2s.com   ngo3@s2s.com
"""
import sys
from datetime import timedelta

from app.auth.security import hash_password
from app.database import Base, SessionLocal, engine
from app import models  # noqa: F401
from app.models.donation import Donation, DonationStatusHistory
from app.models.requirement import Requirement
from app.models.user import User
from app.utils.timeutil import utcnow

PW = "demo1234"


def main(reset: bool):
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    if db.query(User).filter(User.email == "admin@s2s.com").first():
        print("Demo data already present (use --reset to start over).")
        return

    def user(name, email, role, addr, lat, lng, phone):
        u = User(name=name, email=email, password_hash=hash_password(PW), role=role, phone=phone,
                 address=addr, latitude=lat, longitude=lng, verified=True)
        db.add(u); db.flush(); return u

    admin = user("S2S Admin", "admin@s2s.com", "admin", "Kurla West, Mumbai", 19.0728, 72.8826, "9000000000")
    d1 = user("Hotel Sea Breeze", "donor1@s2s.com", "donor", "Colaba, Mumbai", 18.9067, 72.8147, "9000000001")
    d2 = user("Fresh Basket Supermarket", "donor2@s2s.com", "donor", "Bandra West, Mumbai", 19.0596, 72.8295, "9000000002")
    n1 = user("Asha Community Kitchen", "ngo1@s2s.com", "ngo", "Dharavi, Mumbai", 19.0430, 72.8540, "9000000011")
    n2 = user("Roti Bank Mumbai", "ngo2@s2s.com", "ngo", "Andheri East, Mumbai", 19.1136, 72.8697, "9000000012")
    n3 = user("Hope Shelter", "ngo3@s2s.com", "ngo", "Kurla West, Mumbai", 19.0728, 72.8826, "9000000013")

    now = utcnow()
    # requirements spread over the last days so the demand forecast has history
    for ngo, food, kg, urg, pick, days_ago in [
        (n1, "rice", 30, "high", "immediate", 6), (n1, "rice", 35, "high", "immediate", 4),
        (n1, "dal", 15, "medium", "within_2h", 2), (n1, "rice", 40, "high", "immediate", 0),
        (n2, "bread", 20, "medium", "later_today", 5), (n2, "vegetables", 25, "low", "flexible", 3),
        (n2, "rice", 25, "medium", "within_2h", 1),
        (n3, "any", 15, "high", "immediate", 3), (n3, "cooked meals", 30, "high", "within_2h", 0),
    ]:
        r = Requirement(ngo_id=ngo.id, food_type=food, required_quantity_kg=kg, address=ngo.address,
                        latitude=ngo.latitude, longitude=ngo.longitude, urgency=urg,
                        pickup_availability=pick, created_at=now - timedelta(days=days_ago))
        db.add(r)

    def donation(donor, food, kg, serv, hrs, storage, status="posted", ngo=None, ago=1):
        d = Donation(donor_id=donor.id, food_type=food, quantity_kg=kg, servings=serv,
                     prep_time=now - timedelta(hours=ago), expiry_time=now + timedelta(hours=hrs),
                     storage_condition=storage, address=donor.address, latitude=donor.latitude,
                     longitude=donor.longitude, status=status, accepted_ngo_id=ngo.id if ngo else None,
                     fallback_recommendation="none", created_at=now - timedelta(hours=ago))
        db.add(d); db.flush()
        steps = ["posted", "accepted", "pickup_pending", "delivered", "completed"]
        for s in steps[: steps.index(status) + 1] if status in steps else ["posted"]:
            db.add(DonationStatusHistory(donation_id=d.id, status=s, note="demo data"))

    # completed donations -> impact dashboard numbers
    donation(d1, "cooked rice", 40, 160, -2, "refrigerated", "completed", n1, ago=30)
    donation(d1, "dal and curry", 25, 100, -3, "refrigerated", "completed", n1, ago=50)
    donation(d2, "bread", 18, 70, -4, "room_temp", "completed", n2, ago=40)
    donation(d2, "vegetables", 30, 90, -5, "refrigerated", "completed", n2, ago=70)
    # live donations to demo matching / tracking
    donation(d1, "cooked rice", 20, 80, 5, "refrigerated", "posted", ago=1)
    donation(d1, "chapati", 12, 60, 3, "room_temp", "posted", ago=1)
    donation(d2, "mixed vegetables", 22, 70, 20, "refrigerated", "posted", ago=2)
    donation(d2, "bread", 10, 40, 8, "room_temp", "accepted", n3, ago=2)
    db.commit()
    print("Seeded. Log in with e.g. donor1@s2s.com / ngo1@s2s.com / admin@s2s.com  (password: demo1234)")


if __name__ == "__main__":
    main("--reset" in sys.argv)
