# FoodRescue AI (MVP)

A full-stack app connecting surplus-food donors with NGOs/food banks, using a
rule-based "AI" recommendation engine to match donations to the most suitable
NGO based on food type, quantity, distance, and urgency.

## Stack
- **Backend:** Node.js + Express, JSON-file storage (no external DB needed for MVP)
- **Frontend:** Plain HTML/CSS/JS + Leaflet.js (OpenStreetMap) for maps
- **Auth:** JWT + bcrypt password hashing

## Setup

```bash
cd backend
npm install
npm start
```

The server starts on **http://localhost:5000** and also serves the frontend,
so just open that URL in your browser — no separate frontend server needed.

## First-time use

1. Go to `http://localhost:5000`
2. Register a **Donor** account and an **NGO** account (use two different
   browser tabs/windows, or log out and back in).
3. Register an **Admin** account too — admin accounts are auto-verified.
   Donor/NGO accounts need admin verification before they can fully use the
   platform (log in as admin → Manage Users → Verify).
4. As the Donor: post a surplus food donation with a pickup location
   (lat/lng — you can get these from Google Maps by right-clicking a spot).
5. As the NGO: post a food requirement with your location, then check
   "Nearby Available Donations" — the AI recommendation engine will have
   already ranked your requirement against the donation. Click **Accept**.
6. Track the donation through: `posted → accepted → pickup_pending →
   delivered → completed` using the action buttons on the Donor and NGO
   dashboards.
7. Check the Admin dashboard for platform-wide stats.

## Project Structure

```
foodrescue-ai/
├── backend/
│   ├── server.js              # Express app entry point
│   ├── package.json
│   ├── data/                  # JSON "database" files (users, donations, requirements)
│   ├── middleware/auth.js     # JWT auth + role guard
│   ├── utils/
│   │   ├── helpers.js         # file read/write, Haversine distance calc
│   │   └── recommend.js       # AI-based NGO recommendation engine
│   ├── controllers/           # business logic per resource
│   └── routes/                # Express route definitions
└── frontend/
    ├── index.html             # login / register
    ├── donor.html             # donor dashboard
    ├── ngo.html                # NGO dashboard
    ├── admin.html              # admin dashboard
    ├── css/style.css
    └── js/
        ├── api.js             # fetch wrapper + session helpers
        ├── auth.js
        ├── donor.js
        ├── ngo.js
        └── admin.js
```

## Notes on the "AI" recommendation engine

`backend/utils/recommend.js` scores every open NGO requirement against a
newly posted donation using weighted factors:
- Food type match (40 pts)
- Quantity fit (up to 25 pts)
- Distance via the Haversine formula (up to 20 pts, decays with km)
- Urgency level of the NGO's requirement (up to 15 pts)
- Deadline proximity bonus (10 pts if the requirement's deadline is within 24h)

This is intentionally simple and rule-based for the MVP — it's structured so
you can later swap in a real ML-based scoring model without changing the API
shape (`recommendNgosForDonation` returns a ranked array either way).

## Next steps (not in this MVP)
- Push notifications (email/SMS) to NGOs on new matching donations
- Route optimization for volunteers
- Predictive demand modeling
- Real geocoding (address → lat/lng) instead of manual coordinate entry
- Swapping JSON-file storage for a real database (MongoDB/Postgres)
