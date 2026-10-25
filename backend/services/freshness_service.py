from datetime import datetime, timezone


def freshness(item, now=None):
    now = now or datetime.now(timezone.utc)
    value = item.last_synced_at
    if not value:
        return {"status": "unknown", "label": "Last checked not published", "age_days": None}
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    age = max(0, (now - value).days)
    status = "fresh" if age <= 7 else "stale" if age <= 30 else "old"
    return {"status": status, "label": f"Checked {age} day(s) ago", "age_days": age}
