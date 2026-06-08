from datetime import UTC, datetime
from datetime import timedelta
import logging

import asyncpg
import httpx

from app.schemas.market import AllowedInterval, KlineItem
from app.core.config import settings

logger = logging.getLogger(__name__)


class MarketService:
    """Historical market data service with DB-first + Binance REST fallback."""

    _db_pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if MarketService._db_pool is None:
            MarketService._db_pool = await asyncpg.create_pool(
                dsn=settings.postgres_dsn,
                min_size=1,
                max_size=10,
            )
        return MarketService._db_pool

    @staticmethod
    async def _resolve_symbol_id(conn: asyncpg.Connection, symbol: str) -> int:
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
        return int(row["id"])

    @staticmethod
    async def _resolve_interval_id(conn: asyncpg.Connection, interval: str) -> int:
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
        return int(row["id"])

    async def _fetch_from_db(self, symbol: str, interval: AllowedInterval, limit: int) -> list[KlineItem]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    k.timestamp,
                    k.open,
                    k.high,
                    k.low,
                    k.close,
                    k.volume
                FROM klines k
                JOIN symbols s ON s.id = k.symbol_id
                JOIN intervals i ON i.id = k.interval_id
                WHERE s.symbol = $1 AND i.interval = $2
                ORDER BY k.timestamp DESC
                LIMIT $3
                """,
                symbol,
                interval,
                min(limit, settings.max_kline_limit),
            )

        if not rows:
            return []

        # UI requires ascending timeline for chart setData.
        rows = list(reversed(rows))
        return [
            KlineItem(
                timestamp=row["timestamp"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
            for row in rows
        ]

    async def _fetch_from_binance(self, symbol: str, interval: AllowedInterval, limit: int) -> list[KlineItem]:
        capped_limit = min(limit, settings.max_kline_limit)
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": capped_limit,
        }
        url = f"{settings.binance_rest_base_url}/api/v3/klines"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        if not isinstance(payload, list):
            return []

        rows: list[KlineItem] = []
        for item in payload:
            if not isinstance(item, list) or len(item) < 7:
                continue
            close_time_ms = int(item[6])
            rows.append(
                KlineItem(
                    timestamp=datetime.fromtimestamp(close_time_ms / 1000.0, tz=UTC),
                    open=float(item[1]),
                    high=float(item[2]),
                    low=float(item[3]),
                    close=float(item[4]),
                    volume=float(item[5]),
                )
            )
        return rows

    async def _seed_db(self, symbol: str, interval: AllowedInterval, candles: list[KlineItem]) -> None:
        if not candles:
            return

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                symbol_id = await self._resolve_symbol_id(conn, symbol)
                interval_id = await self._resolve_interval_id(conn, interval)

                rows_to_insert = [
                    (
                        candle.timestamp,
                        symbol_id,
                        interval_id,
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                        "fallback",
                        datetime.now(UTC),
                    )
                    for candle in candles
                ]

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

    async def get_historical_klines(
        self,
        *,
        symbol: str,
        interval: AllowedInterval,
        limit: int,
    ) -> list[KlineItem]:
        try:
            db_rows = await self._fetch_from_db(symbol, interval, limit)
        except Exception:
            logger.warning("market_service_db_failed", exc_info=True)
            db_rows = []

        if db_rows:
            return db_rows

        try:
            fallback_rows = await self._fetch_from_binance(symbol, interval, limit)
        except httpx.HTTPError:
            logger.warning("market_service_fallback_failed", exc_info=True)
            fallback_rows = []

        if not fallback_rows:
            return self._build_emergency_mock(symbol, interval, min(limit, settings.max_kline_limit))

        try:
            await self._seed_db(symbol, interval, fallback_rows)
        except Exception:
            logger.warning("market_service_seed_failed", exc_info=True)

        return fallback_rows[-min(limit, len(fallback_rows)) :]

    @staticmethod
    def _build_emergency_mock(
        symbol: str,
        interval: AllowedInterval,
        limit: int,
    ) -> list[KlineItem]:
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
            "1w": 10080,
        }[interval]

        now = datetime.now(UTC)
        base = 60000.0 if symbol == "btcusdt" else 3500.0 if symbol == "ethusdt" else 1000.0
        rows: list[KlineItem] = []
        for i in range(limit):
            t = now - timedelta(minutes=(limit - i) * interval_minutes)
            o = base + i * 0.1
            c = o + 0.2
            h = c + 0.1
            l = o - 0.1
            v = 10.0 + i * 0.01
            rows.append(
                KlineItem(
                    timestamp=t,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v,
                )
            )

        return rows
