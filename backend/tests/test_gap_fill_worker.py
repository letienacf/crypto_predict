import asyncio
from datetime import UTC, datetime

import httpx

from app.schemas.events import GapDetectedEvent, KlineClosedEvent
from app.services.channel_namer import ChannelNamer
from app.services.gap_detector import GapDetector
from app.workers.gap_fill_worker import GapFillWorker


def make_closed_event(close_time: datetime) -> KlineClosedEvent:
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


def make_gap_event() -> GapDetectedEvent:
    detector = GapDetector()
    first = datetime(2026, 6, 5, 10, 0, tzinfo=UTC)
    third = datetime(2026, 6, 5, 10, 3, tzinfo=UTC)

    assert detector.detect_gap(make_closed_event(first)) is None
    gap = detector.detect_gap(make_closed_event(third))
    assert gap is not None
    return gap


class FakeResponse:
    def __init__(self, payload: list[list]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[list]:
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        self.calls: list[dict] = []
        self._responses: list[object] = [
            httpx.TimeoutException("timeout"),
            FakeResponse(
                [
                    [
                        1717581660000,
                        "100.0",
                        "101.0",
                        "99.5",
                        "100.5",
                        "250.0",
                        1717581719999,
                    ]
                ]
            ),
        ]

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, params: dict) -> FakeResponse:
        self.calls.append({"url": url, "params": params})
        next_response = self._responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


class FakeTransaction:
    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.executemany_calls: list[tuple[str, list[tuple]]] = []

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    async def fetchrow(self, query: str, *args) -> dict[str, int]:
        return {"id": 1}

    async def executemany(self, query: str, rows: list[tuple]) -> None:
        self.executemany_calls.append((query, rows))


class FakeAcquire:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakePool:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.connection)


class FakeEventBus:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict]] = []

    async def publish(self, channel: str, payload: dict) -> None:
        self.published.append((channel, payload))


def test_gap_fill_retries_transient_timeout(monkeypatch) -> None:
    worker = GapFillWorker()
    gap = make_gap_event()
    fake_client = FakeAsyncClient()

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    sleep_calls: list[float] = []

    monkeypatch.setattr("app.workers.gap_fill_worker.httpx.AsyncClient", lambda timeout=15.0: fake_client)
    monkeypatch.setattr("app.workers.gap_fill_worker.asyncio.sleep", fake_sleep)

    payload = asyncio.run(worker._fetch_gap_klines(gap))

    assert len(payload) == 1
    assert sleep_calls == [1]
    assert fake_client.calls[0]["params"]["symbol"] == "BTCUSDT"


def test_gap_fill_recovers_gap_and_rebroadcasts(monkeypatch) -> None:
    worker = GapFillWorker()
    gap = make_gap_event()
    connection = FakeConnection()
    pool = FakePool(connection)
    event_bus = FakeEventBus()

    async def fake_resolve_symbol_id(conn, symbol: str) -> int:
        return 1

    async def fake_resolve_interval_id(conn, interval: str) -> int:
        return 1

    monkeypatch.setattr(worker, "_resolve_symbol_id", fake_resolve_symbol_id)
    monkeypatch.setattr(worker, "_resolve_interval_id", fake_resolve_interval_id)

    worker._db_pool = pool
    worker._event_bus = event_bus

    klines = [
        [
            1717581660000,
            "100.0",
            "101.0",
            "99.5",
            "100.5",
            "250.0",
            1717581719999,
        ],
        [
            1717581720000,
            "100.5",
            "102.0",
            "100.2",
            "101.5",
            "180.0",
            1717581779999,
        ],
    ]

    asyncio.run(worker._save_and_rebroadcast(gap, klines))

    assert len(connection.executemany_calls) == 1
    query, rows = connection.executemany_calls[0]
    assert "INSERT INTO klines" in query
    assert len(rows) == 2
    assert rows[0][8] == "recovered"
    assert event_bus.published[0][0] == ChannelNamer.kline_closed("btcusdt", "1m")
    assert event_bus.published[0][1]["event_type"] == "kline.closed"
    assert event_bus.published[0][1]["symbol"] == "btcusdt"