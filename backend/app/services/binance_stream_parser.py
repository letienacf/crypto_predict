from datetime import UTC, datetime

from app.schemas.events import KlineClosedEvent, KlinePartialEvent, TradeTickEvent


class BinanceStreamParser:
    """Parses raw Binance stream payloads into validated event models."""

    @staticmethod
    def _to_datetime_from_ms(value: int | str) -> datetime:
        ms = int(value)
        return datetime.fromtimestamp(ms / 1000.0, tz=UTC)

    def parse_trade_tick(self, payload: dict) -> TradeTickEvent:
        symbol = str(payload["s"]).lower()
        return TradeTickEvent(
            symbol=symbol,
            price=float(payload["p"]),
            quantity=float(payload["q"]),
            trade_time=self._to_datetime_from_ms(payload["T"]),
            ingested_at=datetime.now(UTC),
        )

    def parse_kline(self, payload: dict) -> KlinePartialEvent | KlineClosedEvent:
        kline = payload["k"]
        base_data = {
            "symbol": str(payload["s"]).lower(),
            "interval": str(kline["i"]).lower(),
            "open_time": self._to_datetime_from_ms(kline["t"]),
            "close_time": self._to_datetime_from_ms(kline["T"]),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
            "ingested_at": datetime.now(UTC),
        }

        is_closed = bool(kline["x"])
        if is_closed:
            return KlineClosedEvent(**base_data)
        return KlinePartialEvent(**base_data)
