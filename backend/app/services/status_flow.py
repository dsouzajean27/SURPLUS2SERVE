"""Defines the allowed forward-only donation status transitions (FR10):
Posted -> Accepted -> Pickup Pending -> Delivered -> Completed / Expired
"""

NEXT_ALLOWED = {
    "posted": {"accepted", "expired"},
    "accepted": {"pickup_pending", "expired"},
    "pickup_pending": {"delivered"},
    "delivered": {"completed"},
    "completed": set(),
    "expired": set(),
}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    return new_status in NEXT_ALLOWED.get(current_status, set())
