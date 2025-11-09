from datetime import datetime, timezone, timedelta


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
