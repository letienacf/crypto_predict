from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AllowedInterval = Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w"]


class EventBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_version: Literal[1] = 1


class TradeTickEvent(EventBase):
    event_type: Literal["trade.tick"] = "trade.tick"
    exchange: Literal["binance"] = "binance"
    symbol: str = Field(min_length=3, max_length=20, pattern=r"^[a-z0-9]+$")
    price: float = Field(gt=0)
    quantity: float = Field(gt=0)
    trade_time: datetime
    ingested_at: datetime


class KlineEventBase(EventBase):
    exchange: Literal["binance"] = "binance"
    symbol: str = Field(min_length=3, max_length=20, pattern=r"^[a-z0-9]+$")
    interval: AllowedInterval
    open_time: datetime
    close_time: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    ingested_at: datetime


class KlinePartialEvent(KlineEventBase):
    event_type: Literal["kline.partial"] = "kline.partial"
    is_closed: Literal[False] = False


class KlineClosedEvent(KlineEventBase):
    event_type: Literal["kline.closed"] = "kline.closed"
    is_closed: Literal[True] = True


class GapDetectedEvent(EventBase):
    event_type: Literal["system.gap_detected"] = "system.gap_detected"
    symbol: str = Field(min_length=3, max_length=20, pattern=r"^[a-z0-9]+$")
    interval: AllowedInterval
    from_ts: datetime
    to_ts: datetime
    detected_at: datetime
