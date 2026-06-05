# Crypto Predict

Sprint 1 to Sprint 5 baselines completed from specification documents.

## Delivered scope
- Sprint 1:
  - B1: Contract-first event schemas in contracts/schemas.
  - C1: TimescaleDB migration skeleton in backend/migrations.
  - D2: FastAPI REST skeleton for historical klines endpoint.
  - E1: Frontend hybrid bootstrap (REST load + WebSocket merge) skeleton.
  - F1: CI quality gates for backend and frontend.
- Sprint 2:
  - A1: Binance websocket ingestor worker with reconnect/rotation strategy.
  - A2: Kline close detector and normalized event publishing.
  - B2: Redis channel naming standard implementation.
  - D1: FastAPI websocket market gateway fanout.
- Sprint 3:
  - C2: Data saver worker with Redis subscribe, batch flush, idempotent insert.
  - E2: Realtime candlestick chart rendering using lightweight-charts.
  - E3: Watchlist realtime price updates with 150ms flash effect.
  - G1: Contract tests for event schema and API response schema.
- Sprint 4:
  - A3: Gap detector publishing `system.gap_detected` events.
  - C3: Gap fill worker restores missing candles from Binance REST and patches DB.
  - D3: WebSocket watchlist session management with dynamic `set_watchlist` updates.
  - E4: Live candle O/H/L/C/V stats and server-time-synced countdown.
- Sprint 5:
  - F2: Monitoring metrics, Prometheus alert rules, and runbook.
  - F3: Runtime hardening manifests with probes, resources, restart policies.
  - G2: Latency E2E benchmark and trend artifact generation in CI.

## Structure
- spec: Requirements and planning docs.
- contracts: Event contracts and schema files.
- backend: FastAPI API + DB migration files.
- frontend: React + TypeScript bootstrap application.
- .github/workflows: CI pipeline.

## Quick start
### Backend
- Run from repository root using your Python environment:
  - uvicorn app.main:app --reload --app-dir backend
  - python -m app.workers.binance_ingestor
  - python -m app.workers.data_saver
  - python -m app.workers.gap_fill_worker

### Runtime and Ops
- Docker runtime stack: deploy/docker/docker-compose.runtime.yml
- Kubernetes baseline: deploy/k8s/backend-deployment.yaml
- Prometheus config: ops/prometheus/prometheus.yml
- Alert runbook: ops/runbooks/alerts.md
- Latency benchmark: ops/performance/latency_benchmark.md

### Frontend
- Run from frontend folder:
  - npm install
  - npm run dev

## API example
- GET /api/v1/market/klines?symbol=btcusdt&interval=1m&limit=1000
