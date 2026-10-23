"""Food quality verification (Phase 5) - transparent, rule-based.

Two layers of verification:
  1. assess_quality()   - automatic check from what the donor declared (storage, prep time, packaging,
                          hygiene checklist, photo). Runs live, so the score drops as the food ages.
  2. check_temperature() - recipient inspection at pickup (cold-chain temperature rule).

Like the urgency rules, this is deliberately NOT a black box: every point deducted comes with a
human-readable note. It reduces risk; it does not replace a human looking at the food.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.utils.timeutil import utcnow

CHECKLIST_LABELS = {
    "hygienic_prep": "Prepared in a clean kitchen by people with clean hands",
    "not_plate_leftovers": "NOT leftovers from anyone's plate / buffet that was already served",
    "stored_properly": "Kept at the storage condition stated above the whole time",
    "clean_container": "Packed in a clean, food-grade container",
    "no_spoilage_signs": "No bad smell, mould, slime or discolouration",
}

# Food that grows bacteria quickly if mishandled.
HIGH_RISK_WORDS = ("cooked", "rice", "dal", "curry", "biryani", "meat", "chicken", "fish", "egg",
                   "dairy", "milk", "paneer", "curd", "yogurt", "cream", "pasta", "noodle", "meal",
                   "gravy", "soup", "sandwich", "cake", "pudding", "sweet")

# Hours since preparation after which the food is no longer safe, per storage condition.
# (Room-temp matches urgency.SAFE_WINDOW_HOURS: the "danger zone" rule of thumb is 4 h.)
MAX_AGE_HOURS = {"room_temp": 4, "refrigerated": 48, "frozen": 24 * 30}
WARN_FRACTION = 0.6     # start deducting once 60 % of the safe window is used

GOOD_MIN = 80
CAUTION_MIN = 40

# Cold-chain limits used at pickup inspection (degrees C).
MAX_TEMP_C = {"refrigerated": 5.0, "frozen": -15.0}


def is_high_risk(food_type: str) -> bool:
    t = (food_type or "").lower()
    return any(w in t for w in HIGH_RISK_WORDS)


def assess_quality(food_type: str, storage_condition: str, prep_time: Optional[datetime],
                   expiry_time: datetime, packaging: Optional[str], checklist: Optional[dict],
                   has_photo: bool, now: Optional[datetime] = None) -> dict:
    """Returns {"score": 0-100, "status": good|caution|rejected, "notes": [...], "blockers": [...]}.

    blockers  = reasons the food must not be donated at all (status becomes 'rejected').
    notes     = everything that reduced the score, shown to donor and recipient.
    """
    now = now or utcnow()
    storage = storage_condition or "room_temp"
    risky = is_high_risk(food_type)
    score = 100
    notes, blockers = [], []

    # --- 1. Time safety ---------------------------------------------------
    if expiry_time <= now:
        blockers.append("Expiry time has already passed.")
    if prep_time:
        limit = MAX_AGE_HOURS.get(storage, 4)
        age_h = (now - prep_time).total_seconds() / 3600
        # Low-risk food (raw veg, packaged items) gets a more generous window.
        eff_limit = limit if (risky or storage != "room_temp") else limit * 3
        if age_h > eff_limit:
            blockers.append(
                f"Prepared {age_h:.1f} h ago - beyond the {eff_limit:g} h safe window for "
                f"{storage.replace('_', ' ')} storage.")
        elif age_h > eff_limit * WARN_FRACTION:
            used = age_h / eff_limit
            penalty = int(10 + 30 * (used - WARN_FRACTION) / (1 - WARN_FRACTION))
            score -= penalty
            notes.append(f"{used * 100:.0f}% of the safe window is used up ({age_h:.1f} h since preparation).")
    elif risky and storage != "frozen":
        score -= 15
        notes.append("Preparation time not given for perishable food - safe window cannot be checked.")

    # --- 2. Storage / packaging ------------------------------------------
    if risky and storage == "room_temp":
        score -= 10
        notes.append("Perishable food kept at room temperature - should be delivered quickly.")
    pack_penalty = {"sealed": 0, "covered": 5, "open": 15, None: 5}
    p = pack_penalty.get(packaging, 5)
    if p:
        score -= p
        notes.append("Packaging not stated." if packaging is None else
                     f"Packaging is '{packaging}' - sealed containers are safest.")

    # --- 3. Donor hygiene declaration ------------------------------------
    if checklist is None:
        score -= 25
        notes.append("Donor has not completed the food-safety checklist.")
    else:
        if checklist.get("not_plate_leftovers") is False:
            blockers.append("Food that was already served on plates / buffets cannot be donated.")
        if checklist.get("no_spoilage_signs") is False:
            blockers.append("Donor reports signs of spoilage (smell, mould, slime or discolouration).")
        for key, pts in (("hygienic_prep", 20), ("stored_properly", 20), ("clean_container", 10)):
            if checklist.get(key) is False:
                score -= pts
                notes.append(f"Not confirmed: {CHECKLIST_LABELS[key]}.")

    # --- 4. Evidence -------------------------------------------------------
    if not has_photo:
        score -= 5
        notes.append("No photo uploaded - recipients cannot visually check the food beforehand.")

    score = max(0, min(100, score))
    if blockers or score < CAUTION_MIN:
        status = "rejected"
    elif score < GOOD_MIN:
        status = "caution"
    else:
        status = "good"
    return {"score": score, "status": status, "notes": notes, "blockers": blockers}


def check_temperature(storage_condition: str, temperature_c: Optional[float]) -> Optional[str]:
    """Returns a warning string if the measured temperature breaks the cold-chain limit, else None."""
    limit = MAX_TEMP_C.get(storage_condition)
    if temperature_c is None or limit is None:
        return None
    if storage_condition == "refrigerated" and temperature_c > limit:
        return f"{temperature_c:g} °C is above the {limit:g} °C limit for refrigerated food."
    if storage_condition == "frozen" and temperature_c > limit:
        return f"{temperature_c:g} °C is above the {limit:g} °C limit for frozen food."
    return None


def assess_donation(d, now: Optional[datetime] = None) -> dict:
    """Convenience wrapper that runs assess_quality() on a Donation ORM object."""
    return assess_quality(d.food_type, d.storage_condition, d.prep_time, d.expiry_time,
                          d.packaging, d.hygiene_checklist, bool(d.image_url), now)
