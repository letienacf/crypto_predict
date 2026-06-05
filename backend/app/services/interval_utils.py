from datetime import timedelta

from app.schemas.events import AllowedInterval

_INTERVAL_TO_SECONDS: dict[AllowedInterval, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
}


def interval_to_timedelta(interval: AllowedInterval) -> timedelta:
    return timedelta(seconds=_INTERVAL_TO_SECONDS[interval])
