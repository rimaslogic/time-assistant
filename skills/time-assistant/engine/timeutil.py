"""Timezone helpers. Time-source timestamps (Toggl, etc.) are UTC; convert to
the tenant's timezone (from config) before bucketing or displaying."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def to_zone(iso_ts: str, tz_name: str) -> str:
    """Convert an ISO-8601 timestamp to `tz_name`, returning an ISO string with offset.
    Accepts trailing 'Z' and naive timestamps (assumed UTC). Falls back to UTC if
    tz_name is unknown."""
    s = iso_ts.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        zone = timezone.utc
    return dt.astimezone(zone).isoformat()
