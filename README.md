# Surplus2Serve — Backend (Phases 1–2)

AI-based surplus food redistribution platform. Matches the report's stack:
**React.js (frontend, not built yet) + Python/FastAPI (backend) + MySQL (database) + Scikit-learn (AI/ML, coming in Phase 3)**.

This delivery covers:
- **Phase 1:** Project scaffold, MySQL connection, User/Donation/Requirement/Notification models, JWT auth (register/login)
- **Phase 2:** Donation posting & listing, NGO requirement posting & listing, donation acceptance, and full status tracking (Posted → Accepted → Pickup Pending → Delivered → Completed/Expired) with an audit history table

Everything below has been tested against a real local MySQL instance.

## 1. Install MySQL (if you don't have it)

**Windows:** install MySQL Community Server from dev.mysql.com, or via `choco install mysql`.
**Mac:** `brew install mysql && brew services start mysql`
**Linux:** `sudo apt install mysql-server && sudo service mysql start`

## 2. Create the database and a dev user

Open a MySQL shell (`mysql -u root -p`) and run:

```sql
CREATE DATABASE surplus2serve;
CREATE USER 's2s_user'@'localhost' IDENTIFIED BY 's2s_pass123';
GRANT ALL PRIVILEGES ON surplus2serve.* TO 's2s_user'@'localhost';
FLUSH PRIVILEGES;
```

(These exact credentials match the included `backend/.env` file, so no further config is needed — but feel free to change them, just update `.env` to match.)

## 3. Install Python dependencies

```bash
cd backend
pip install -r requirements.txt
```

If you don't already have Python 3.10+, install it first.

## 4. Run the server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

On startup, FastAPI automatically creates all tables in your `surplus2serve` database (no migration step needed for this prototype). Visit `http://localhost:8000/docs` for the interactive Swagger UI — you can test every endpoint from the browser without writing any frontend code yet.

## Project structure

```
backend/
├── requirements.txt
├── .env                        # DB credentials + JWT secret (already filled in for local dev)
├── .env.example
└── app/
    ├── main.py                 # FastAPI app entrypoint, creates tables, mounts routers
    ├── config.py                # Settings loaded from .env
    ├── database.py              # SQLAlchemy engine/session (MySQL)
    ├── models/                  # SQLAlchemy ORM models
    │   ├── user.py
    │   ├── donation.py          # Donation + DonationStatusHistory
    │   ├── requirement.py
    │   └── notification.py      # (model ready; endpoints come in a later phase)
    ├── schemas/                 # Pydantic request/response validation
    │   ├── user.py
    │   ├── donation.py
    │   └── requirement.py
    ├── auth/
    │   ├── security.py          # bcrypt password hashing + JWT
    │   └── dependencies.py      # get_current_user, require_role(...)
    ├── routers/                 # API endpoints
    │   ├── auth.py               # POST /api/auth/register, /api/auth/login
    │   ├── donations.py          # POST/GET /api/donations, PATCH .../status
    │   └── requirements.py       # POST/GET/DELETE /api/requirements
    ├── services/
    │   └── status_flow.py        # Valid donation status transitions
    └── utils/
        └── geo.py                 # Haversine distance calculation
```

## API endpoints so far

| Method | Path | Role required | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | — | Register as donor / ngo / admin |
| POST | `/api/auth/login` | — | Log in, get a JWT |
| POST | `/api/donations` | donor | Post a surplus food donation |
| GET | `/api/donations` | any | List donations (`mine=true`, `status_filter=`, `near_lat`/`near_lng`/`max_distance_km`) |
| GET | `/api/donations/{id}` | any | Get one donation |
| PATCH | `/api/donations/{id}/status` | donor/ngo/admin | Move a donation through its status flow |
| POST | `/api/requirements` | ngo | Post a food requirement |
| GET | `/api/requirements` | any | List requirements (`mine=true`) |
| DELETE | `/api/requirements/{id}` | ngo/admin | Delete a requirement |

All endpoints except register/login require `Authorization: Bearer <token>`.

## What's next (not in this delivery yet)

- Phase 3: AI recommendation engine (Scikit-learn)
- Phase 4: Urgency/expiry engine + circular-economy fallback
- Phase 5: Location/route suggestion + demand prediction (Scikit-learn)
- Phase 6: Notifications + impact dashboard + admin dashboard
- Phase 7: React frontend
