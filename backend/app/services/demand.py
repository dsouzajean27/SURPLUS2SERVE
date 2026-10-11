"""Demand analysis / prediction (FR16) with scikit-learn LinearRegression."""
from collections import defaultdict
from datetime import timedelta
from typing import List, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression


def predict_demand(history: Sequence[Tuple[float, float]], horizon: int = 7) -> List[float]:
    """history: [(day_index, quantity), ...] -> predicted quantity for the next `horizon` days.
    With fewer than 2 points a regression is impossible, so the mean is used."""
    if not history:
        return [0.0] * horizon
    xs = np.array([h[0] for h in history], dtype=float).reshape(-1, 1)
    ys = np.array([h[1] for h in history], dtype=float)
    last = float(xs.max())
    future = np.arange(last + 1, last + 1 + horizon, dtype=float).reshape(-1, 1)
    if len(history) < 2 or len(set(xs.ravel().tolist())) < 2:
        return [round(float(ys.mean()), 2)] * horizon
    model = LinearRegression().fit(xs, ys)
    return [round(max(0.0, float(p)), 2) for p in model.predict(future)]


def daily_history(requirements, food_type: str | None = None):
    """Aggregates historical requirement quantities per day. Returns (dates, quantities)."""
    totals = defaultdict(float)
    for r in requirements:
        if food_type and food_type != "all" and r.food_type.lower() != food_type.lower():
            continue
        totals[r.created_at.date()] += r.required_quantity_kg
    if not totals:
        return [], []
    start, end = min(totals), max(totals)
    days = (end - start).days + 1
    dates = [start + timedelta(days=i) for i in range(days)]
    return dates, [round(totals.get(d, 0.0), 2) for d in dates]


def forecast_for(requirements, food_type: str | None = None, horizon: int = 7):
    dates, qty = daily_history(requirements, food_type)
    history = list(zip(range(len(dates)), qty))
    preds = predict_demand(history, horizon)
    future_dates = [(dates[-1] + timedelta(days=i + 1)) if dates else None for i in range(horizon)]
    return {
        "food_type": food_type or "all",
        "history": [{"date": d.isoformat(), "quantity_kg": q} for d, q in zip(dates, qty)],
        "forecast": [
            {"date": d.isoformat() if d else None, "quantity_kg": p} for d, p in zip(future_dates, preds)
        ],
        "method": "LinearRegression" if len(history) >= 2 else "mean (not enough history)",
        "expected_total_kg_next_7_days": round(sum(preds), 2),
    }
