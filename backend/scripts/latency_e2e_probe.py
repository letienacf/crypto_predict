import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

import redis.asyncio as aioredis
import websockets


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    rank = (len(sorted_values) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def run_probe(ws_url: str, redis_url: str, symbol: str, interval: str, sample_size: int) -> dict:
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
    channel = f"market:kline.closed:{symbol}:{interval}"

    latencies_ms: list[float] = []
    receive_task: asyncio.Task | None = None

    try:
        async with websockets.connect(ws_url) as ws:
            await ws.send(
                json.dumps(
                    {
                        "action": "set_watchlist",
                        "symbols": [symbol],
                        "intervals": [interval],
                    }
                )
            )

            async def receiver() -> None:
                while len(latencies_ms) < sample_size:
                    raw = await ws.recv()
                    payload = json.loads(raw)
                    if payload.get("event_type") != "kline.closed":
                        continue
                    ingested_at = payload.get("ingested_at")
                    if not isinstance(ingested_at, str):
                        continue
                    start = datetime.fromisoformat(ingested_at.replace("Z", "+00:00"))
                    delta_ms = (datetime.now(UTC) - start).total_seconds() * 1000.0
                    if delta_ms >= 0:
                        latencies_ms.append(delta_ms)

            receive_task = asyncio.create_task(receiver())

            for idx in range(sample_size):
                ts = datetime.now(UTC)
                close_ts = datetime.fromtimestamp(ts.timestamp() + idx, tz=UTC)
                payload = {
                    "event_type": "kline.closed",
                    "event_version": 1,
                    "exchange": "binance",
                    "symbol": symbol,
                    "interval": interval,
                    "open_time": ts.isoformat(),
                    "close_time": close_ts.isoformat(),
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.5,
                    "close": 100.5,
                    "volume": 42.0,
                    "is_closed": True,
                    "ingested_at": now_iso(),
                }
                await redis_client.publish(channel, json.dumps(payload, separators=(",", ":")))
                await asyncio.sleep(0.01)

            await asyncio.wait_for(receive_task, timeout=15)

        p50 = percentile(latencies_ms, 0.50)
        p95 = percentile(latencies_ms, 0.95)
        p99 = percentile(latencies_ms, 0.99)
        result = {
            "timestamp": now_iso(),
            "sample_size": len(latencies_ms),
            "mean_ms": round(mean(latencies_ms), 3) if latencies_ms else 0.0,
            "p50_ms": round(p50, 3),
            "p95_ms": round(p95, 3),
            "p99_ms": round(p99, 3),
            "target_ms": 300,
            "ideal_ms": 150,
        }
        return result
    finally:
        if receive_task is not None:
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass
        await redis_client.aclose()


def write_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Latency E2E probe for websocket fanout")
    parser.add_argument("--ws-url", default="ws://localhost:8000/ws/market?symbols=btcusdt&intervals=1m")
    parser.add_argument("--redis-url", default="redis://localhost:6379/0")
    parser.add_argument("--symbol", default="btcusdt")
    parser.add_argument("--interval", default="1m")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--assert-p95-ms", type=float, default=300.0)
    parser.add_argument(
        "--output",
        default="reports/latency/latest.json",
        help="Path relative to backend folder",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    report = await run_probe(
        ws_url=args.ws_url,
        redis_url=args.redis_url,
        symbol=args.symbol,
        interval=args.interval,
        sample_size=args.sample_size,
    )

    output = Path(args.output)
    write_report(report, output)

    print(json.dumps(report, indent=2))
    if report["p95_ms"] > args.assert_p95_ms:
        raise SystemExit(2)


if __name__ == "__main__":
    asyncio.run(main())
