from datetime import UTC, datetime

from app.schemas.events import KlineClosedEvent
from app.services.gap_detector import GapDetector


def make_event(close_time: datetime) -> KlineClosedEvent:
    return KlineClosedEvent(
        symbol="btcusdt",
        interval="1m",
        open_time=close_time,
        close_time=close_time,
        open=1.0,
        high=1.2,
        low=0.9,
        close=1.1,
        volume=100.0,
        ingested_at=close_time,
    )


def test_gap_detector_no_gap_for_continuous_candles() -> None:
    detector = GapDetector()

    t1 = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 6, 5, 10, 1, tzinfo=UTC)

    assert detector.detect_gap(make_event(t1)) is None
    assert detector.detect_gap(make_event(t2)) is None


def test_gap_detector_detects_missing_window() -> None:
    detector = GapDetector()

    t1 = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
    t3 = datetime(2026, 6, 5, 10, 3, tzinfo=UTC)

    assert detector.detect_gap(make_event(t1)) is None
    gap = detector.detect_gap(make_event(t3))

    assert gap is not None
    assert gap.symbol == "btcusdt"
    assert gap.interval == "1m"
    assert gap.from_ts == datetime(2026, 6, 5, 10, 1, tzinfo=UTC)
    assert gap.to_ts == t3
