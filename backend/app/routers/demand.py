from fastapi import APIRouter
from app.services.demand import predict_demand

router = APIRouter(prefix="/api/demand", tags=["demand"])

@router.post("/predict")
def predict(history: list[tuple[int, int]]):
    """
    history: JSON array of [day_index, quantity]
    """
    forecast = predict_demand(history)
    return {"forecast": forecast}
