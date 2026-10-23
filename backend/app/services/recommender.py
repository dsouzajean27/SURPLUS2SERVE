"""AI-based recipient recommendation (FR06).

For one donation, every open NGO requirement is scored 0-1 on five factors
and the weighted sum is used to rank the recipients:

  food compatibility  0.30   TF-IDF n-gram similarity (scikit-learn) + food-category knowledge
  quantity fit        0.15   can the NGO use the whole donation?
  distance            0.20   haversine distance, decays with km
  urgency / pickup    0.15   urgent food -> NGOs that can collect quickly & need it urgently
  recipient demand    0.10   how much the NGO still needs (relative to the other candidates)
  reliability         0.10   learned from history: completed pickups vs accepted-but-expired

Hard rules (a recipient is dropped, not just scored lower, when):
  * food compatibility is below FOOD_GATE, or
  * it cannot physically get there before the food's safe window ends
    (travel time at AVG_SPEED_KMH > hours left).
The AI only ranks *who* should get the food; it never decides food safety.
"""
import re
from typing import Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.urgency import classify_urgency
from app.utils.geo import haversine_distance
from app.utils.timeutil import utcnow

WEIGHTS = {"food": 0.30, "quantity": 0.15, "distance": 0.20, "urgency_pickup": 0.15,
           "demand": 0.10, "reliability": 0.10}
FOOD_GATE = 0.25
ANY_SCORE = 0.5
SAME_CATEGORY_SCORE = 0.7   # e.g. donation "roti" vs requirement "chapati"
NEUTRAL_RELIABILITY = 0.5   # NGOs with no history are neither rewarded nor punished
AVG_SPEED_KMH = 20.0        # urban pickup speed used for the "can they reach it in time" rule

# Food-category knowledge: lets "roti" match a "chapati" need, which text similarity alone cannot.
FOOD_CATEGORIES = {
    "cooked_meal": ["rice", "biryani", "pulao", "dal", "curry", "sabzi", "khichdi", "meal", "lunch",
                    "dinner", "thali", "pasta", "noodle", "cooked", "poha", "upma"],
    "bread": ["bread", "roti", "chapati", "chapatti", "naan", "paratha", "bun", "pav", "toast", "sandwich"],
    "vegetables": ["vegetable", "veggie", "potato", "onion", "tomato", "spinach", "carrot", "salad", "cabbage"],
    "fruits": ["fruit", "apple", "banana", "mango", "orange", "grape", "papaya"],
    "dairy": ["milk", "curd", "yogurt", "yoghurt", "paneer", "cheese", "butter"],
    "bakery": ["cake", "pastry", "biscuit", "cookie", "muffin", "cupcake"],
    "packaged": ["packaged", "packet", "canned", "snack", "chips", "juice"],
    "grains": ["wheat", "flour", "atta", "pulses", "lentil", "grain", "cereal"],
}


def food_category(text: str):
    t = (text or "").lower()
    for cat, words in FOOD_CATEGORIES.items():
        if any(re.search(rf"\b{w}", t) for w in words):
            return cat
    return None

PICKUP_SCORE = {
    "high": {"immediate": 1.0, "within_2h": 0.8, "later_today": 0.4, "flexible": 0.2},
    "medium": {"immediate": 0.9, "within_2h": 0.9, "later_today": 0.7, "flexible": 0.5},
    "low": {"immediate": 0.8, "within_2h": 0.9, "later_today": 1.0, "flexible": 1.0},
}
REQ_URGENCY_SCORE = {"high": 1.0, "medium": 0.6, "low": 0.3}


def _food_similarity(donation_food: str, req_foods: List[str]) -> List[float]:
    d = (donation_food or "").strip().lower()
    reqs = [(r or "").strip().lower() for r in req_foods]
    if not reqs:
        return []
    try:
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        m = vec.fit_transform([d] + reqs)
        sims = cosine_similarity(m[0:1], m[1:]).ravel().tolist()
    except ValueError:  # empty vocabulary
        sims = [0.0] * len(reqs)
    out = []
    for s, r in zip(sims, reqs):
        if r == d:
            out.append(1.0)
        elif r in ("any", "all", "anything", "any food"):
            out.append(ANY_SCORE)
        else:
            cat_d, cat_r = food_category(d), food_category(r)
            if cat_d and cat_d == cat_r:
                s = max(float(s), SAME_CATEGORY_SCORE)
            out.append(round(float(s), 4))
    return out


def _explain(b: Dict[str, float], dist_km: float) -> str:
    labels = {"food": "food type match", "quantity": "quantity fit", "distance": f"close by ({dist_km:.1f} km)",
              "urgency_pickup": "pickup/urgency fit", "demand": "high demand",
              "reliability": "good pickup track record"}
    top = sorted(b.items(), key=lambda kv: kv[1] * WEIGHTS[kv[0]], reverse=True)[:2]
    return "Best on " + " and ".join(labels[k] for k, _ in top)


def rank_recipients(donation, requirements, top_k: Optional[int] = 5, now=None,
                    reliability: Optional[Dict[str, float]] = None) -> List[dict]:
    """Ranks open requirements (one best entry per NGO) for a donation.
    `reliability` maps ngo_id -> 0..1 (see services.donations.ngo_reliability_map)."""
    now = now or utcnow()
    reliability = reliability or {}
    reqs = [r for r in requirements if r.deadline is None or r.deadline > now]
    if not reqs:
        return []
    urg = classify_urgency(donation.expiry_time, donation.prep_time, donation.storage_condition, now)
    sims = _food_similarity(donation.food_type, [r.food_type for r in reqs])

    pool = [(r, s) for r, s in zip(reqs, sims) if s >= FOOD_GATE]
    if not pool:
        return []
    max_req = max(r.required_quantity_kg for r, _ in pool) or 1.0

    best_per_ngo: Dict[str, dict] = {}
    for r, food in pool:
        dist = haversine_distance(donation.latitude, donation.longitude, r.latitude, r.longitude)
        # Feasibility: can the NGO get there before the safe window closes?
        if urg["hours_left"] > 0 and dist / AVG_SPEED_KMH > urg["hours_left"]:
            continue
        qty = min(1.0, r.required_quantity_kg / donation.quantity_kg) if donation.quantity_kg else 0.0
        b = {
            "food": food,
            "quantity": qty,
            "distance": 1.0 / (1.0 + dist / 5.0),
            "urgency_pickup": 0.5 * PICKUP_SCORE[urg["level"]].get(r.pickup_availability, 0.5)
            + 0.5 * REQ_URGENCY_SCORE.get(r.urgency, 0.3),
            "demand": r.required_quantity_kg / max_req,
            "reliability": reliability.get(r.ngo_id, NEUTRAL_RELIABILITY),
        }
        score = sum(WEIGHTS[k] * v for k, v in b.items())
        item = {
            "ngo_id": r.ngo_id,
            "ngo_name": r.ngo.name if getattr(r, "ngo", None) else None,
            "requirement_id": r.id,
            "score": round(score * 100, 1),
            "distance_km": dist,
            "breakdown": {k: round(v * 100, 1) for k, v in b.items()},
            "requirement": {
                "food_type": r.food_type,
                "required_quantity_kg": r.required_quantity_kg,
                "urgency": r.urgency,
                "pickup_availability": r.pickup_availability,
                "address": r.address,
            },
            "explanation": _explain(b, dist),
        }
        cur = best_per_ngo.get(r.ngo_id)
        if cur is None or item["score"] > cur["score"]:
            best_per_ngo[r.ngo_id] = item

    ranked = sorted(best_per_ngo.values(), key=lambda x: x["score"], reverse=True)
    for i, it in enumerate(ranked, 1):
        it["rank"] = i
    return ranked[:top_k] if top_k else ranked


def rank_donations_for_ngo(donations, ngo_requirements, reliability: Optional[Dict[str, float]] = None) -> List[dict]:
    """NGO view: which available donations suit this NGO's requirements best.
    Returns [{donation, score, distance_km, breakdown, explanation}] best first."""
    out = []
    for d in donations:
        ranked = rank_recipients(d, ngo_requirements, top_k=None, reliability=reliability)
        if ranked:
            best = ranked[0]
            out.append({"donation": d, "score": best["score"], "distance_km": best["distance_km"],
                        "breakdown": best["breakdown"], "explanation": best["explanation"],
                        "requirement_id": best["requirement_id"]})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out
