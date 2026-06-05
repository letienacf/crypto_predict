from datetime import datetime

from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram
from prometheus_client import generate_latest

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=("method", "path", "status"),
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1, 2, 5),
)

ws_connections_active = Gauge(
    "ws_connections_active",
    "Active WebSocket market connections",
)

ws_messages_sent_total = Counter(
    "ws_messages_sent_total",
    "WebSocket messages sent to clients",
    labelnames=("event_type",),
)

ws_broadcast_latency_seconds = Histogram(
    "ws_broadcast_latency_seconds",
    "End-to-end broadcast latency using event ingested_at timestamp",
    labelnames=("event_type",),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1),
)

ingestor_reconnect_total = Counter(
    "ingestor_reconnect_total",
    "Number of Binance ingestor reconnect attempts",
)

ingestor_parse_error_total = Counter(
    "ingestor_parse_error_total",
    "Number of parse/validation errors in Binance ingestor",
)

gap_detected_total = Counter(
    "gap_detected_total",
    "Number of detected stream gaps",
    labelnames=("symbol", "interval"),
)

gap_fill_requests_total = Counter(
    "gap_fill_requests_total",
    "Number of gap-fill REST requests",
    labelnames=("symbol", "interval"),
)

gap_fill_records_total = Counter(
    "gap_fill_records_total",
    "Number of recovered candles written to database",
    labelnames=("symbol", "interval"),
)

gap_fill_failures_total = Counter(
    "gap_fill_failures_total",
    "Number of gap-fill failures",
    labelnames=("reason",),
)

data_saver_flush_total = Counter(
    "data_saver_flush_total",
    "Number of data saver flush operations",
)

data_saver_records_total = Counter(
    "data_saver_records_total",
    "Number of records written by data saver",
)


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def observe_ws_event_latency(event_type: str, ingested_at_raw: str | None) -> None:
    if ingested_at_raw is None:
        return

    parsed = _parse_iso_datetime(ingested_at_raw)
    if parsed is None:
        return

    latency_seconds = (datetime.now(parsed.tzinfo) - parsed).total_seconds()
    if latency_seconds >= 0:
        ws_broadcast_latency_seconds.labels(event_type=event_type).observe(latency_seconds)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
