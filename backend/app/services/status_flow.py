"""Allowed forward-only donation status transitions (FR10):
Posted -> Accepted -> Pickup Pending -> Delivered -> Completed / Expired
"""

NEXT_ALLOWED = {
    "posted": {"accepted", "expired"},
    "accepted": {"pickup_pending", "expired"},
    "pickup_pending": {"delivered", "expired"},
    "delivered": {"completed"},
    "completed": set(),
    "expired": set(),
}

# Statuses in which an unrecovered donation can still run out of time.
EXPIRABLE = {"posted", "accepted", "pickup_pending"}
FINAL = {"completed", "expired"}


def is_valid_transition(current_status: str, new_status: str) -> bool:
    return new_status in NEXT_ALLOWED.get(current_status, set())
