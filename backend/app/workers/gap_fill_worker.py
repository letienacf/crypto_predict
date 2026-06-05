import asyncio
import json
import logging
from datetime import UTC, datetime

import asyncpg
import httpx
import redis.asyncio as aioredis
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.observability.metrics import gap_fill_failures_total
from app.observability.metrics import gap_fill_records_total
from app.observability.metrics import gap_fill_requests_total
from app.schemas.events import GapDetectedEvent, KlineClosedEvent
from app.services.channel_namer import ChannelNamer
from app.services.redis_event_bus import RedisEventBus

logger = logging.getLogger(__name__)


class GapFillWorker:
    """C3 worker: recover missing closed candles from Binance REST after gap detection."""

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._db_pool: asyncpg.Pool | None = None
        self._event_bus = RedisEventBus(settings.redis_url)
        self._symbol_id_cache: dict[str, int] = {}
        self._interval_id_cache: dict[str, int] = {}

    async def connect(self) -> None:
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.psubscribe("system:gap_detected:*:*")
        self._db_pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=10)
        await self._event_bus.connect()

    async def close(self) -> None:
        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None

        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

        if self._db_pool is not None:
            await self._db_pool.close()
            self._db_pool = None

        await self._event_bus.close()

    async def _resolve_symbol_id(self, conn: asyncpg.Connection, symbol: str) -> int:
        cached = self._symbol_id_cache.get(symbol)
        if cached is not None:
            return cached

        row = await conn.fetchrow(
            """
            INSERT INTO symbols (symbol, base_asset, quote_asset)
            VALUES ($1, $2, $3)
            ON CONFLICT (symbol) DO UPDATE SET symbol = EXCLUDED.symbol
            RETURNING id
            """,
            symbol,
            symbol[:-4] if len(symbol) > 4 else symbol,
            symbol[-4:] if len(symbol) > 4 else "usdt",
        )
        if row is None:
            raise RuntimeError("Failed to resolve symbol id")

        symbol_id = int(row["id"])
        self._symbol_id_cache[symbol] = symbol_id
        return symbol_id

    async def _resolve_interval_id(self, conn: asyncpg.Connection, interval: str) -> int:
        cached = self._interval_id_cache.get(interval)
        if cached is not None:
            return cached

        row = await conn.fetchrow(
            """
            INSERT INTO intervals (interval)
            VALUES ($1)
            ON CONFLICT (interval) DO UPDATE SET interval = EXCLUDED.interval
            RETURNING id
            """,
            interval,
        )
        if row is None:
            raise RuntimeError("Failed to resolve interval id")

        interval_id = int(row["id"])
        self._interval_id_cache[interval] = interval_id
        return interval_id

    async def _fetch_gap_klines(self, gap: GapDetectedEvent) -> list[list]:
        start_ms = int(gap.from_ts.timestamp() * 1000)
        end_ms = int(gap.to_ts.timestamp() * 1000)
        params = {
            "symbol": gap.symbol.upper(),
            "interval": gap.interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": settings.gap_fill_max_klines_per_request,
        }

        url = f"{settings.binance_rest_base_url}/api/v3/klines"
        async with httpx.AsyncClient(timeout=15.0) as client:
            gap_fill_requests_total.labels(symbol=gap.symbol, interval=gap.interval).inc()
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                return []
            return payload

    async def _save_and_rebroadcast(self, gap: GapDetectedEvent, klines: list[list]) -> None:
        if self._db_pool is None:
            return

        if not klines:
            return

        async with self._db_pool.acquire() as conn:
            async with conn.transaction():
                symbol_id = await self._resolve_symbol_id(conn, gap.symbol)
                interval_id = await self._resolve_interval_id(conn, gap.interval)

                rows_to_insert: list[tuple] = []
                rebroadcast_events: list[KlineClosedEvent] = []
                for row in klines:
                    if len(row) < 7:
                        continue
                    open_time_ms = int(row[0])
                    close_time_ms = int(row[6])

                    close_time = datetime.fromtimestamp(close_time_ms / 1000.0, tz=UTC)
                    rows_to_insert.append(
                        (
                            close_time,
                            symbol_id,
                            interval_id,
                            float(row[1]),
                            float(row[2]),
                            float(row[3]),
                            float(row[4]),
                            float(row[5]),
                            "recovered",
                            datetime.now(UTC),
                        )
                    )

                    rebroadcast_events.append(
                        KlineClosedEvent(
                            symbol=gap.symbol,
                            interval=gap.interval,
                            open_time=datetime.fromtimestamp(open_time_ms / 1000.0, tz=UTC),
                            close_time=close_time,
                            open=float(row[1]),
                            high=float(row[2]),
                            low=float(row[3]),
                            close=float(row[4]),
                            volume=float(row[5]),
                            ingested_at=datetime.now(UTC),
                        )
                    )

                if rows_to_insert:
                    await conn.executemany(
                        """
                        INSERT INTO klines (
                            timestamp,
                            symbol_id,
                            interval_id,
                            open,
                            high,
                            low,
                            close,
                            volume,
                            source,
                            created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (timestamp, symbol_id, interval_id) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            source = EXCLUDED.source
                        """,
                        rows_to_insert,
                    )

        for event in rebroadcast_events:
            channel = ChannelNamer.kline_closed(event.symbol, event.interval)
            await self._event_bus.publish(channel, event.model_dump(mode="json"))

        if rebroadcast_events:
            gap_fill_records_total.labels(symbol=gap.symbol, interval=gap.interval).inc(
                len(rebroadcast_events)
            )
            logger.info(
                "gap_fill_persisted",
                extra={"symbol": gap.symbol, "interval": gap.interval, "records": len(rebroadcast_events)},
            )

    async def run_forever(self) -> None:
        await self.connect()
        try:
            if self._pubsub is None:
                return

            async for message in self._pubsub.listen():
                if message.get("type") not in {"message", "pmessage"}:
                    continue

                raw_data = message.get("data")
                if not isinstance(raw_data, str):
                    continue

                try:
                    payload = json.loads(raw_data)
                    gap = GapDetectedEvent.model_validate(payload)
                except (json.JSONDecodeError, ValidationError):
                    continue

                try:
                    klines = await self._fetch_gap_klines(gap)
                    await self._save_and_rebroadcast(gap, klines)
                except (httpx.HTTPError, ValueError, RuntimeError):
                    gap_fill_failures_total.labels(reason="runtime_error").inc()
                    logger.warning("gap_fill_failed", exc_info=True)
                    continue
        finally:
            await self.close()


async def main() -> None:
    setup_logging(settings.log_level)
    worker = GapFillWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
