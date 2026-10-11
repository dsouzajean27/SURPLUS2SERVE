from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.requirement import Requirement
from app.models.user import User
from app.services.demand import predict_demand, forecast_for

router = APIRouter(prefix="/api/demand", tags=["demand"])


class DemandHistory(BaseModel):
    history: List[List[float]]  # [[day_index, quantity], ...]


@router.post("/predict")
def predict(body: DemandHistory, current_user: User = Depends(get_current_user)):
    """Forecast the next 7 days from an explicit history (handy for Postman demos)."""
    return {"forecast": predict_demand([(h[0], h[1]) for h in body.history if len(h) == 2])}


@router.get("/forecast")
def forecast(food_type: Optional[str] = None, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    """FR16 - forecast recipient demand (kg/day) for the next 7 days from the
    historical requirements stored in the database."""
    reqs = db.query(Requirement).all()
    result = forecast_for(reqs, food_type)
    result["food_types"] = sorted({r.food_type.lower() for r in reqs})
    return result
