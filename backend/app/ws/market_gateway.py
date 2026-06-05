import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

import redis.asyncio as aioredis
from fastapi import WebSocket

from app.core.config import settings
from app.observability.metrics import observe_ws_event_latency
from app.observability.metrics import ws_connections_active
from app.observability.metrics import ws_messages_sent_total

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ClientSubscription:
    websocket: WebSocket
    symbols: set[str]
    intervals: set[str]
    connected_at: datetime
    updated_at: datetime


class MarketGateway:
    """D1 gateway: fanout Redis events to active WebSocket clients."""

    def __init__(self) -> None:
        self._clients: dict[int, ClientSubscription] = {}
        self._lock = asyncio.Lock()
        self._running_task: asyncio.Task | None = None
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None

    @property
    def is_ready(self) -> bool:
        return self._redis is not None and self._pubsub is not None and self._running_task is not None

    async def start(self) -> None:
        if self._running_task is not None:
            return

        try:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            self._pubsub = self._redis.pubsub()
            await self._pubsub.psubscribe(
                "market:trade.tick:*",
                "market:kline.partial:*:*",
                "market:kline.closed:*:*",
            )
            self._running_task = asyncio.create_task(self._run(), name="market-gateway-redis-loop")
        except Exception:
            logger.warning("market_gateway_start_failed", exc_info=True)
            if self._pubsub is not None:
                await self._pubsub.aclose()
                self._pubsub = None
            if self._redis is not None:
                await self._redis.aclose()
                self._redis = None
            self._running_task = None

    async def stop(self) -> None:
        if self._running_task is not None:
            self._running_task.cancel()
            try:
                await self._running_task
            except asyncio.CancelledError:
                pass
            self._running_task = None

        if self._pubsub is not None:
            await self._pubsub.aclose()
            self._pubsub = None

        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def connect(self, websocket: WebSocket, *, symbols: set[str], intervals: set[str]) -> None:
        await websocket.accept()

        if len(symbols) > settings.ws_max_symbols_per_session:
            symbols = set(sorted(symbols)[: settings.ws_max_symbols_per_session])
        if len(intervals) > settings.ws_max_intervals_per_session:
            intervals = set(sorted(intervals)[: settings.ws_max_intervals_per_session])

        sub = ClientSubscription(
            websocket=websocket,
            symbols={s.lower() for s in symbols},
            intervals={i.lower() for i in intervals},
            connected_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        async with self._lock:
            self._clients[id(websocket)] = sub
            ws_connections_active.set(len(self._clients))

    async def update_watchlist(
        self,
        websocket: WebSocket,
        *,
        symbols: set[str],
        intervals: set[str],
    ) -> None:
        if len(symbols) > settings.ws_max_symbols_per_session:
            symbols = set(sorted(symbols)[: settings.ws_max_symbols_per_session])
        if len(intervals) > settings.ws_max_intervals_per_session:
            intervals = set(sorted(intervals)[: settings.ws_max_intervals_per_session])

        async with self._lock:
            sub = self._clients.get(id(websocket))
            if sub is None:
                return
            sub.symbols = {s.lower() for s in symbols}
            sub.intervals = {i.lower() for i in intervals}
            sub.updated_at = datetime.now(UTC)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.pop(id(websocket), None)
            ws_connections_active.set(len(self._clients))

    async def _run(self) -> None:
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
            except json.JSONDecodeError:
                continue

            await self._broadcast(payload)

    async def _broadcast(self, payload: dict) -> None:
        symbol = str(payload.get("symbol", "")).lower()
        interval = str(payload.get("interval", "")).lower()
        event_type = str(payload.get("event_type", "unknown"))
        ingested_at_raw = payload.get("ingested_at")
        if isinstance(ingested_at_raw, str):
            observe_ws_event_latency(event_type=event_type, ingested_at_raw=ingested_at_raw)

        async with self._lock:
            clients = list(self._clients.values())

        for sub in clients:
            if sub.symbols and symbol and symbol not in sub.symbols:
                continue
            if sub.intervals and interval and interval not in sub.intervals:
                continue
            try:
                await sub.websocket.send_json(payload)
                ws_messages_sent_total.labels(event_type=event_type).inc()
            except Exception:
                logger.warning("websocket_send_failed", exc_info=True)
                await self.disconnect(sub.websocket)
