from datetime import datetime
from app.utils.geo import haversine_distance
from app.services.urgency import classify_urgency, fallback_use

def compute_score(donation, requirement):
    # Food type match
    food_match = 1.0 if donation.food_type == requirement.food_type else 0.0

    # Quantity match (closer is better)
    qty_diff = abs(donation.quantity - requirement.quantity)
    qty_score = 1.0 / (1.0 + qty_diff)

    # Distance score
    dist_km = haversine_distance(donation.lat, donation.lng,
                                 requirement.lat, requirement.lng)
    dist_score = 1.0 / (1.0 + dist_km)

    # Expiry/urgency score
    expiry_days = (donation.expiry_date - datetime.now()).days
    urgency_score = 1.0 / (1.0 + abs(expiry_days - requirement.urgency_days))

    # Weighted sum
    final_score = (0.4 * food_match +
                   0.2 * qty_score +
                   0.2 * dist_score +
                   0.2 * urgency_score)
    return final_score

def recommend(donations, requirements, top_k=3):
    recommendations = {}
    for req in requirements:
        scored = [(don, compute_score(don, req)) for don in donations]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored[:top_k]

        if not top_matches:
            # No matches → fallback
            recommendations[req.id] = [{
                "donation_id": None,
                "suggestion": fallback_use(req.food_type)
            }]
        else:
            recommendations[req.id] = [{
                "donation_id": d.id,
                "score": s,
                "urgency": classify_urgency(d.expiry_date)
            } for d, s in top_matches]
    return recommendations

