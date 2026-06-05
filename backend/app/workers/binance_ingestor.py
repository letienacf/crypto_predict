import asyncio
import json
import logging
import random
from collections.abc import Iterable

import websockets
from pydantic import ValidationError

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.schemas.events import GapDetectedEvent
from app.schemas.events import KlineClosedEvent, KlinePartialEvent, TradeTickEvent
from app.observability.metrics import gap_detected_total
from app.observability.metrics import ingestor_parse_error_total
from app.observability.metrics import ingestor_reconnect_total
from app.services.binance_stream_parser import BinanceStreamParser
from app.services.channel_namer import ChannelNamer
from app.services.gap_detector import GapDetector
from app.services.redis_event_bus import RedisEventBus

logger = logging.getLogger(__name__)


class BinanceIngestorWorker:
    """A1+A2+B2 worker: consume Binance WS and publish normalized Redis events."""

    def __init__(self) -> None:
        self._parser = BinanceStreamParser()
        self._event_bus = RedisEventBus(settings.redis_url)
        self._gap_detector = GapDetector()

    @staticmethod
    def _build_streams(symbols: Iterable[str], intervals: Iterable[str]) -> list[str]:
        normalized_symbols = [s.strip().lower() for s in symbols if s.strip()]
        normalized_intervals = [i.strip().lower() for i in intervals if i.strip()]

        streams: list[str] = []
        for symbol in normalized_symbols:
            streams.append(f"{symbol}@aggTrade")
            for interval in normalized_intervals:
                streams.append(f"{symbol}@kline_{interval}")
        return streams

    async def _handle_event(self, event: dict) -> None:
        event_name = event.get("e")
        if event_name == "aggTrade":
            parsed = self._parser.parse_trade_tick(event)
            channel = ChannelNamer.trade_tick(parsed.symbol)
            await self._event_bus.publish(channel, parsed.model_dump(mode="json"))
            return

        if event_name == "kline":
            parsed_kline = self._parser.parse_kline(event)
            if isinstance(parsed_kline, KlineClosedEvent):
                channel = ChannelNamer.kline_closed(parsed_kline.symbol, parsed_kline.interval)
            elif isinstance(parsed_kline, KlinePartialEvent):
                channel = ChannelNamer.kline_partial(parsed_kline.symbol, parsed_kline.interval)
            else:
                return
            await self._event_bus.publish(channel, parsed_kline.model_dump(mode="json"))

            if settings.enable_gap_detection and isinstance(parsed_kline, KlineClosedEvent):
                gap_event = self._gap_detector.detect_gap(parsed_kline)
                if isinstance(gap_event, GapDetectedEvent):
                    gap_channel = ChannelNamer.gap_detected(gap_event.symbol, gap_event.interval)
                    await self._event_bus.publish(gap_channel, gap_event.model_dump(mode="json"))
                    gap_detected_total.labels(
                        symbol=gap_event.symbol,
                        interval=gap_event.interval,
                    ).inc()

    async def _stream_once(self, stream_url: str) -> None:
        async with websockets.connect(stream_url, ping_interval=20, ping_timeout=20) as ws:
            start_loop_time = asyncio.get_running_loop().time()
            while True:
                now = asyncio.get_running_loop().time()
                if now - start_loop_time >= settings.binance_connection_rotation_seconds:
                    return

                raw_message = await ws.recv()
                try:
                    envelope = json.loads(raw_message)
                    data = envelope.get("data")
                    if not isinstance(data, dict):
                        continue
                    await self._handle_event(data)
                except (json.JSONDecodeError, KeyError, TypeError, ValueError, ValidationError):
                    # Drop malformed messages to keep stream alive.
                    ingestor_parse_error_total.inc()
                    continue

    async def run_forever(self) -> None:
        await self._event_bus.connect()

        symbols = settings.stream_symbols
        intervals = settings.stream_intervals
        streams = self._build_streams(symbols, intervals)
        if not streams:
            raise RuntimeError("No Binance streams configured")

        stream_url = f"{settings.binance_ws_base_url}/stream?streams={'/'.join(streams)}"

        attempt = 0
        try:
            while True:
                try:
                    await self._stream_once(stream_url)
                    attempt = 0
                except Exception:
                    attempt += 1
                    ingestor_reconnect_total.inc()
                    base = min(settings.reconnect_max_seconds, 2 ** attempt)
                    sleep_seconds = base + random.uniform(0, 0.5)
                    logger.warning("binance_ingestor_reconnect", extra={"attempt": attempt})
                    await asyncio.sleep(sleep_seconds)
        finally:
            await self._event_bus.close()


async def main() -> None:
    setup_logging(settings.log_level)
    worker = BinanceIngestorWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
