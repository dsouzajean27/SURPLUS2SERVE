from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.migrations import ensure_columns
from app import models  # noqa: F401 - registers all models with Base before create_all
from app.routers import (auth, donations, requirements, recommendations, dashboard,
                         demand, notifications, routes, admin, location, uploads, messages)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates tables that don't exist yet; never alters existing ones.
    # Fine for a college prototype - use Alembic migrations for production.
    Base.metadata.create_all(bind=engine)
    ensure_columns(engine, Base)   # adds any new columns to tables that already exist
    yield


app = FastAPI(title="Surplus2Serve API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, donations, requirements, recommendations, dashboard, demand,
          notifications, routes, admin, location, uploads, messages):
    app.include_router(r.router)

# Uploaded food photos are served publicly from /uploads/<file>
app.mount("/uploads", StaticFiles(directory=uploads.UPLOAD_DIR), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
