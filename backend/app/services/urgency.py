"""Urgency & expiry management (FR08) - transparent, rule-based.

Inputs: preparation time, expiry/best-before, storage condition, now.
Cooked food has a safe-holding window that depends on how it is stored,
so the *effective* deadline is the earlier of the stated expiry and
prep_time + safe-window.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.utils.timeutil import utcnow

SAFE_WINDOW_HOURS = {"room_temp": 4, "refrigerated": 48, "frozen": 24 * 30}
HIGH_HOURS = 6
MEDIUM_HOURS = 24


def hours_left(expiry_time: datetime, prep_time: Optional[datetime] = None,
               storage_condition: str = "room_temp", now: Optional[datetime] = None) -> float:
    now = now or utcnow()
    deadline = expiry_time
    if prep_time:
        deadline = min(deadline, prep_time + timedelta(hours=SAFE_WINDOW_HOURS.get(storage_condition, 4)))
    return round((deadline - now).total_seconds() / 3600, 2)


def classify_urgency(expiry_time: datetime, prep_time: Optional[datetime] = None,
                     storage_condition: str = "room_temp", now: Optional[datetime] = None) -> dict:
    """Returns {"level": low|medium|high, "hours_left": float, "reason": str}."""
    h = hours_left(expiry_time, prep_time, storage_condition, now)
    if h <= HIGH_HOURS:
        level = "high"
    elif h <= MEDIUM_HOURS:
        level = "medium"
    else:
        level = "low"
    if h <= 0:
        reason = "Safe/expiry window has passed"
    else:
        reason = f"About {h:.1f} h left ({storage_condition.replace('_', ' ')} storage)"
    return {"level": level, "hours_left": h, "reason": reason}


# ---- Circular-economy fallback (FR12) --------------------------------------
_COMPOST_WORDS = ("peel", "scrap", "vegetable", "veggie", "fruit", "leaves", "salad", "waste")
_FEED_WORDS = ("cooked", "rice", "roti", "chapati", "bread", "dal", "curry", "biryani", "meat",
               "chicken", "fish", "egg", "dairy", "milk", "paneer", "pasta", "noodle", "grain", "meal")


def fallback_use(food_type: str) -> str:
    """Returns 'compost' or 'animal_feed' (values of the Donation.fallback_recommendation enum)."""
    t = (food_type or "").lower()
    if any(w in t for w in _COMPOST_WORDS):
        return "compost"
    if any(w in t for w in _FEED_WORDS):
        return "animal_feed"
    return "compost"


FALLBACK_TEXT = {
    "compost": "No suitable recipient found. Recommended recovery: composting (turn the food into soil nutrients).",
    "animal_feed": "No suitable recipient found. Recommended recovery: animal feed (send to a farm / animal shelter if still safe for animals).",
    "none": "",
}
