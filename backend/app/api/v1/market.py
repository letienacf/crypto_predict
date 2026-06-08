from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.market import AllowedInterval, KlineQuery, KlineResponse
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


def get_market_service() -> MarketService:
    # Dependency inversion: route depends on abstraction boundary.
    return MarketService()


@router.get("/klines", response_model=KlineResponse)
async def get_historical_klines(
    symbol: Annotated[str, Query(min_length=3, max_length=20, pattern=r"^[a-z0-9]+$")],
    interval: Annotated[AllowedInterval, Query(...)],
    service: Annotated[MarketService, Depends(get_market_service)],
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
) -> KlineResponse:
    query = KlineQuery(symbol=symbol, interval=interval, limit=limit)
    data = await service.get_historical_klines(
        symbol=query.symbol,
        interval=query.interval,
        limit=query.limit,
    )
    return KlineResponse(status="success", data=data)
