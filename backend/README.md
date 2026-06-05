# Backend Sprint 1

Implemented in Sprint 1:
- D2 skeleton: REST endpoint GET /api/v1/market/klines with strict validation.
- C1 baseline: DB migration files for metadata + hypertables.

Implemented in Sprint 2:
- A1: Binance WebSocket ingestion worker with reconnect/backoff and connection rotation.
- A2: Kline close detection (`x=true`) with normalized realtime event payload.
- B2: Redis channel naming and publish flow.
- D1: WebSocket market gateway with server-side symbol/interval filtering.

Implemented in Sprint 3:
- C2: Data saver worker for Redis `kline.closed` stream with batch persistence.
- G1: Contract tests validating event and API payloads against JSON Schemas.

Implemented in Sprint 4:
- A3: Gap detection publishing `system.gap_detected` events.
- C3: Gap fill worker calling Binance REST and patching missing candles.
- D3: Dynamic watchlist session updates via websocket control messages.
- E4: Server-synced countdown and live candle stats support.

Implemented in Sprint 5:
- F2: Prometheus metrics endpoint, alert rules, and operational runbook.
- F3: Runtime hardening manifests (Docker Compose and Kubernetes deployment probes/resources).
- G2: Automated latency benchmark probe with p50/p95/p99 reports and CI artifact trend.

Run locally:
1. Install dependencies with your preferred Python workflow.
2. Run API: uvicorn app.main:app --reload --app-dir backend
3. Run ingestion worker: python -m app.workers.binance_ingestor
4. Run data saver worker: python -m app.workers.data_saver
5. Run gap fill worker: python -m app.workers.gap_fill_worker

Observability endpoints:
- GET /metrics
- GET /healthz
- GET /readyz
