# Alert Runbook

## BackendHighErrorRate
- Check recent deployment changes and rollback if needed.
- Inspect backend logs for 5xx stack traces and failing routes.
- Verify downstream dependencies (Redis, TimescaleDB, Binance API).

## IngestorReconnectSpike
- Confirm network stability to Binance websocket endpoint.
- Inspect reconnect logs and parse error counters.
- If persistent, reduce stream set and fail over to backup network path.

## WebsocketLatencyP95TooHigh
- Check ws_connections_active and ws_messages_sent_total volume.
- Inspect backend CPU and memory saturation.
- Scale gateway replicas and verify Redis latency.

## GapFillFailing
- Verify Binance REST availability and response status.
- Check database write permissions and connection pool limits.
- Replay failed gap windows after incident is resolved.

## MemoryUsageTooHigh
- Capture process heap snapshot and identify long-lived allocations.
- Check queue growth and websocket connection fanout pressure.
- Restart affected service and open incident for memory leak analysis.
