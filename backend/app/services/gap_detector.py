from datetime import UTC, datetime

from app.schemas.events import GapDetectedEvent, KlineClosedEvent
from app.services.interval_utils import interval_to_timedelta


class GapDetector:
    """Detects missing closed-candle windows for each symbol/interval stream."""

    def __init__(self) -> None:
        self._last_close_time: dict[tuple[str, str], datetime] = {}

    def detect_gap(self, event: KlineClosedEvent) -> GapDetectedEvent | None:
        key = (event.symbol, event.interval)
        previous = self._last_close_time.get(key)
        self._last_close_time[key] = event.close_time

        if previous is None:
            return None

        expected_next = previous + interval_to_timedelta(event.interval)
        if event.close_time <= expected_next:
            return None

        return GapDetectedEvent(
            symbol=event.symbol,
            interval=event.interval,
            from_ts=expected_next,
            to_ts=event.close_time,
            detected_at=datetime.now(UTC),
        )
