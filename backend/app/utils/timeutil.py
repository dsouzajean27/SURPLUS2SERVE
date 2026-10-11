from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC 'now' - all datetimes in the DB are stored as naive UTC."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
