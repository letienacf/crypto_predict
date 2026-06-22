from contextlib import asynccontextmanager
import json
from datetime import UTC
from datetime import datetime
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.responses import JSONResponse

from app.api.v1.market import router as market_router
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.observability.metrics import http_request_duration_seconds
from app.observability.metrics import http_requests_total
from app.observability.metrics import render_metrics
from app.services.market_service import MarketService
from app.ws.market_gateway import MarketGateway

setup_logging(settings.log_level)

market_gateway = MarketGateway()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.historical_cache_enabled:
        try:
            await MarketService.preload_historical_cache()
        except Exception:
            logging.getLogger(__name__).warning(
                "historical_cache_prewarm_failed",
                exc_info=True,
            )
    await market_gateway.start()
    try:
        yield
    finally:
        await market_gateway.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(market_router, prefix=settings.api_prefix)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    started = perf_counter()
    path = request.url.path
    method = request.method
    status = "500"

    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    except Exception:
        http_requests_total.labels(method=method, path=path, status=status).inc()
        http_request_duration_seconds.labels(method=method, path=path).observe(perf_counter() - started)
        raise
    finally:
        if status != "500":
            http_requests_total.labels(method=method, path=path, status=status).inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(
                perf_counter() - started
            )


@app.get("/healthz", tags=["system"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["system"])
async def readyz() -> JSONResponse:
    # Gateway connection to Redis is the critical readiness dependency.
    is_ready = market_gateway.is_ready
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "not_ready"},
    )


@app.get("/api/v1/system/time", tags=["system"])
async def server_time() -> dict[str, str]:
    return {"server_time": datetime.now(UTC).isoformat()}


@app.get("/metrics", tags=["system"])
async def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@app.websocket("/ws/market")
async def ws_market(
    websocket: WebSocket,
    symbols: str = "",
    intervals: str = "",
) -> None:
    symbol_set = {item.strip().lower() for item in symbols.split(",") if item.strip()}
    interval_set = {item.strip().lower() for item in intervals.split(",") if item.strip()}

    await market_gateway.connect(
        websocket,
        symbols=symbol_set,
        intervals=interval_set,
    )

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            if not isinstance(payload, dict):
                continue

            action = payload.get("action")
            if action != "set_watchlist":
                continue

            new_symbols_raw = payload.get("symbols", [])
            new_intervals_raw = payload.get("intervals", [])
            if not isinstance(new_symbols_raw, list) or not isinstance(new_intervals_raw, list):
                continue

            new_symbols = {str(item).strip().lower() for item in new_symbols_raw if str(item).strip()}
            new_intervals = {
                str(item).strip().lower() for item in new_intervals_raw if str(item).strip()
            }
            await market_gateway.update_watchlist(
                websocket,
                symbols=new_symbols,
                intervals=new_intervals,
            )

            await websocket.send_json(
                {
                    "event_type": "watchlist.updated",
                    "symbols": sorted(new_symbols),
                    "intervals": sorted(new_intervals),
                }
            )
    except WebSocketDisconnect:
        await market_gateway.disconnect(websocket)
