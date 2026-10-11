from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app import models  # noqa: F401 - imported so all models register with Base before create_all
from app.routers import auth, donations, requirements, recommendations, dashboard, demand, notifications, routes

app = FastAPI(title="Surplus2Serve API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before any real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Creates tables that don't exist yet; does not alter existing ones.
    # Fine for a college-project prototype - use Alembic migrations for production.
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(donations.router)
app.include_router(requirements.router)
app.include_router(recommendations.router)
app.include_router(dashboard.router)
app.include_router(demand.router)
app.include_router(routes.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
