# Architecture

## Tổng quan
Crypto Predict là một hệ thống realtime market gateway cho dữ liệu Binance, gồm:
- Backend FastAPI cung cấp REST API và WebSocket gateway.
- Worker ingest dữ liệu realtime từ Binance WebSocket.
- Redis làm event bus trung tâm.
- TimescaleDB/PostgreSQL lưu trữ candles lịch sử.
- Frontend React/Vite hiển thị biểu đồ realtime và watchlist.

## Các thành phần chính

### 1) Binance Ingestor Worker
- Chạy tại `backend/app/workers/binance_ingestor.py`.
- Kết nối tới Binance WebSocket public.
- Thu thập sự kiện `aggTrade` và `kline`.
- Chuyển đổi thành schema nội bộ:
  - `market.trade.tick`
  - `market.kline.partial`
  - `market.kline.closed`
- Đẩy sự kiện vào Redis Pub/Sub qua `RedisEventBus`.
- Thực hiện gap detection dựa trên candle `kline.closed`.
- Khi phát hiện mất dữ liệu, publish thêm sự kiện `system.gap_detected`.

### 2) Redis Event Bus
- Sử dụng `redis.asyncio` làm nguồn Pub/Sub trung tâm.
- Worker dữ liệu và gateway WebSocket thao tác qua các channel chuẩn.
- Channel naming chuẩn được định nghĩa trong `backend/app/services/channel_namer.py`.

### 3) Data Saver Worker
- Chạy tại `backend/app/workers/data_saver.py`.
- Subscribe vào channel `market:kline.closed:*:*`.
- Batch lưu candle vào TimescaleDB/PostgreSQL.
- Bảo đảm idempotency với `ON CONFLICT DO NOTHING`.
- Lưu metadata `source = live`.

### 4) Gap Fill Worker
- Chạy tại `backend/app/workers/gap_fill_worker.py`.
- Subscribe vào channel `system:gap_detected:*:*`.
- Khi nhận gap event, gọi Binance REST `/api/v3/klines`.
- Patch lại các candles thiếu vào DB và rebroadcast event nếu cần.

### 5) FastAPI Backend + WebSocket Gateway
- Chạy tại `backend/app/main.py`.
- Cung cấp REST API:
  - `GET /api/v1/market/klines`
  - `GET /api/v1/system/time`
  - `GET /healthz`
  - `GET /readyz`
  - `GET /metrics`
- Cung cấp WebSocket realtime tại `/ws/market`.
- Gateway subscribe Redis channels:
  - `market:trade.tick:*`
  - `market:kline.partial:*:*`
  - `market:kline.closed:*:*`
- Fanout payload tới client theo filter `symbols` và `intervals`.
- Hỗ trợ cập nhật watchlist runtime với action `set_watchlist`.

### 6) Frontend
- Nằm trong `frontend/`.
- React + TypeScript + Vite.
- Hiển thị candlestick chart, live candle stats và watchlist realtime.
- Frontend load dữ liệu lịch sử qua `/api/v1/market/klines` và cập nhật realtime qua `/ws/market`.

## Dòng dữ liệu
1. Binance WebSocket gửi event về worker ingest.
2. Worker parse event, publish vào Redis.
3. DataSaver worker persist candle closed vào TimescaleDB.
4. MarketGateway lắng nghe Redis và broadcast tới WebSocket clients.
5. Frontend nhận dữ liệu realtime và cập nhật UI.

## Schema và hợp đồng dữ liệu
- Event payload và REST schema được định nghĩa trong `backend/app/schemas/`.
- REST response model: `KlineResponse` chứa danh sách `KlineItem`.
- Interval hợp lệ: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`.

## Quan sát và vận hành
- Metrics Prometheus có sẵn tại `GET /metrics`.
- Health check:
  - `GET /healthz`
  - `GET /readyz`
- Backend sử dụng Prometheus client để đo:
  - HTTP requests
  - WebSocket latency
  - worker events

## Triển khai
- Runtime chính bằng Docker Compose: `deploy/docker/docker-compose.runtime.yml`.
- Kubernetes baseline: `deploy/k8s/backend-deployment.yaml`.
- Prometheus config: `ops/prometheus/prometheus.yml`.
- Alert rules: `ops/prometheus/alert_rules.yml`.
- Runbook alert: `ops/runbooks/alerts.md`.
