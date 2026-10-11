# Surplus2Serve - AI-Based Surplus Food Redistribution Platform

Stack (as in the project report): **React.js** · **Python + FastAPI** · **MySQL** · **scikit-learn** · **JWT** · **OpenStreetMap (Nominatim geocoding + OSRM routing + Leaflet maps)**.

## Run it

### 1. MySQL
```sql
CREATE DATABASE surplus2serve;
CREATE USER 's2s_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON surplus2serve.* TO 's2s_user'@'localhost';
FLUSH PRIVILEGES;
```
### 2. Backend
```bash
cd backend
copy .env.example .env        # (cp on Mac/Linux) then put your DB password + a random JWT secret in .env
pip install -r requirements.txt
python seed_demo.py           # optional demo data (add --reset to wipe & reseed)
uvicorn app.main:app --reload --port 8000     # Swagger UI: http://localhost:8000/docs
```
Tables are created automatically on startup.
### 3. Frontend
```bash
cd frontend
npm install
npm start                     # http://localhost:3000
```
### Demo logins (after `seed_demo.py`, password `demo1234`)
`admin@s2s.com` · `donor1@s2s.com` · `donor2@s2s.com` · `ngo1@s2s.com` · `ngo2@s2s.com` · `ngo3@s2s.com`
Admin self-registration needs the code in `ADMIN_SIGNUP_CODE` (default `S2S-ADMIN-2026`).

### Tests
```bash
cd backend && pip install -r requirements-dev.txt && python -m pytest tests -v
```
(23 automated tests, mapped to report test cases TC01-TC14; they use an in-memory SQLite DB, no MySQL needed.)

## Requirement coverage
| FR | Feature | Where |
|---|---|---|
| FR01-02 | Register/login (JWT, bcrypt), roles, profile | `routers/auth.py`, `Login.js`, `Profile.js` |
| FR03,05 | Post/list/edit/delete surplus food | `routers/donations.py`, `PostDonation.js` |
| FR04 | NGO requirements | `routers/requirements.py`, `Requirements.js` |
| FR06 | AI recipient recommendation (scikit-learn TF-IDF similarity + weighted multi-factor ranking) | `services/recommender.py` |
| FR07 | Geocoding + distance | `utils/geo.py`, `routers/location.py` |
| FR08 | Urgency & expiry rules | `services/urgency.py` |
| FR09-10 | Accept + Posted→Accepted→Pickup Pending→Delivered→Completed/Expired with audit trail | `services/status_flow.py`, `DonationDetail.js` |
| FR11 | Route (OSRM) + multi-donor collection trip | `routers/routes.py`, `Pickups.js` |
| FR12 | Circular economy fallback (compost / animal feed) | `services/urgency.py` |
| FR13 | Notifications (in-app + optional SMTP e-mail) | `services/notifications.py`, `Notifications.js` |
| FR14 | Impact dashboard | `services/impact.py`, `Impact.js` |
| FR15 | Admin dashboard (users, verify, donations, activity) | `routers/admin.py`, `Admin.js` |
| FR16 | Demand forecast (scikit-learn LinearRegression) | `services/demand.py`, `Demand.js` |
| FR17 | Donation history | `GET /api/donations/{id}/history` |
