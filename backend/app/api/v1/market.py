from fastapi import APIRouter, Depends, Query

from app.schemas.market import KlineQuery, KlineResponse
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


def get_market_service() -> MarketService:
    # Dependency inversion: route depends on abstraction boundary.
    return MarketService()


@router.get("/klines", response_model=KlineResponse)
async def get_historical_klines(
    symbol: str = Query(..., min_length=3, max_length=20, pattern=r"^[a-z0-9]+$"),
    interval: str = Query(...),
    limit: int = Query(default=1000, ge=1, le=5000),
    service: MarketService = Depends(get_market_service),
) -> KlineResponse:
    query = KlineQuery(symbol=symbol, interval=interval, limit=limit)
    data = await service.get_historical_klines(
        symbol=query.symbol,
        interval=query.interval,
        limit=query.limit,
    )
    return KlineResponse(status="success", data=data)
