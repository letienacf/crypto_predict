from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AllowedInterval = Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w"]


class KlineQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    symbol: str = Field(min_length=3, max_length=20, pattern=r"^[a-z0-9]+$")
    interval: AllowedInterval
    limit: int = Field(default=1000, ge=1, le=5000)


class KlineItem(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @field_validator("open", "high", "low", "close", "volume", mode="before")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate that prices are valid numbers (not NaN, not infinite)."""
        if not isinstance(v, (int, float)):
            raise ValueError(f"Price must be a number, got {type(v)}")
        if v < 0:
            raise ValueError(f"Price cannot be negative: {v}")
        if not (0 <= v <= 1e10):
            raise ValueError(f"Price out of acceptable range: {v}")
        return float(v)


class KlineResponse(BaseModel):
    status: Literal["success"]
    data: list[KlineItem]
