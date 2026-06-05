from datetime import datetime, timedelta, timezone

from app.schemas.market import AllowedInterval, KlineItem


class MarketService:
    """Service boundary for market data retrieval.

    Sprint 1 returns deterministic mock data to unblock frontend handoff.
    Team C will replace this with asyncpg query implementation in Sprint 2+.
    """

    async def get_historical_klines(
        self,
        *,
        symbol: str,
        interval: AllowedInterval,
        limit: int,
    ) -> list[KlineItem]:
        # Mock data keeps API stable while DB layer is in progress.
        now = datetime.now(timezone.utc)
        base = 100000.0 if symbol == "btcusdt" else 1000.0

        rows: list[KlineItem] = []
        for i in range(limit):
            t = now - timedelta(minutes=(limit - i))
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

        _ = interval  # kept for interface parity and future route-to-repo logic
        return rows
