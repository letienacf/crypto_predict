import asyncio
import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import asyncpg
import redis.asyncio as aioredis
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.observability.metrics import data_saver_flush_total
from app.observability.metrics import data_saver_records_total
from app.schemas.events import KlineClosedEvent

logger = logging.getLogger(__name__)


class DataSaverWorker:
    """C2 worker: consume closed candles and persist in TimescaleDB with batching."""

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._db_pool: asyncpg.Pool | None = None
        self._batch: list[KlineClosedEvent] = []
        self._batch_lock = asyncio.Lock()
        self._symbol_id_cache: dict[str, int] = {}
        self._interval_id_cache: dict[str, int] = {}

    async def connect(self) -> None:
        self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.psubscribe("market:kline.closed:*:*")
        self._db_pool = await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=1, max_size=10)

    async def close(self) -> None:
        await self.flush_to_db()

        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None

        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

        if self._db_pool is not None:
            await self._db_pool.close()
            self._db_pool = None

    async def _listen_messages(self) -> AsyncIterator[dict]:
        if self._pubsub is None:
            return
        async for message in self._pubsub.listen():
            if message.get("type") not in {"message", "pmessage"}:
                continue
            data = message.get("data")
            if isinstance(data, str):
                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload

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

    async def flush_to_db(self) -> None:
        if self._db_pool is None:
            return

        async with self._batch_lock:
            if not self._batch:
                return
            records = self._batch.copy()
            self._batch.clear()

        async with self._db_pool.acquire() as conn:
            async with conn.transaction():
                rows_to_insert: list[tuple] = []
                for event in records:
                    symbol_id = await self._resolve_symbol_id(conn, event.symbol)
                    interval_id = await self._resolve_interval_id(conn, event.interval)
                    rows_to_insert.append(
                        (
                            event.close_time,
                            symbol_id,
                            interval_id,
                            event.open,
                            event.high,
                            event.low,
                            event.close,
                            event.volume,
                            "live",
                            datetime.now(UTC),
                        )
                    )

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
                    ON CONFLICT (timestamp, symbol_id, interval_id) DO NOTHING
                    """,
                    rows_to_insert,
                )
                data_saver_flush_total.inc()
                data_saver_records_total.inc(len(rows_to_insert))
                logger.info("data_saver_flush", extra={"records": len(rows_to_insert)})

    async def run_forever(self) -> None:
        await self.connect()

        periodic_task = asyncio.create_task(self._periodic_flush(), name="data-saver-periodic-flush")
        try:
            async for payload in self._listen_messages():
                try:
                    event = KlineClosedEvent.model_validate(payload)
                except ValidationError:
                    continue

                async with self._batch_lock:
                    if len(self._batch) >= settings.data_saver_max_batch_size:
                        self._batch.pop(0)
                    self._batch.append(event)
                    should_flush = len(self._batch) >= settings.data_saver_batch_size

                if should_flush:
                    await self.flush_to_db()
        finally:
            periodic_task.cancel()
            try:
                await periodic_task
            except asyncio.CancelledError:
                pass
            await self.close()

    async def _periodic_flush(self) -> None:
        while True:
            await asyncio.sleep(settings.data_saver_flush_seconds)
            await self.flush_to_db()


async def main() -> None:
    setup_logging(settings.log_level)
    worker = DataSaverWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
