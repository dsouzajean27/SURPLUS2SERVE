from datetime import datetime

def classify_urgency(expiry_date: datetime) -> str:
    days_left = (expiry_date - datetime.now()).days

    if days_left <= 1:
        return "High"
    elif days_left <= 3:
        return "Medium"
    else:
        return "Low"

def fallback_use(food_type: str) -> str:
    if food_type in ["vegetables", "fruits", "grains"]:
        return "Compost or animal feed"
    elif food_type in ["packaged", "canned"]:
        return "Recycling or food bank redistribution"
    else:
        return "General waste management"
