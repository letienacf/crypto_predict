# Setup

## Yêu cầu môi trường
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose (nếu dùng container runtime)
- Redis và TimescaleDB nếu chạy backend ngoài Docker

## Thiết lập backend
1. Chuyển vào thư mục backend:
   ```bash
   cd backend
   ```

2. Tạo virtual environment và cài đặt:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -e .
   ```

3. Biến môi trường cấu hình (tuỳ chọn):
   - `CP_POSTGRES_DSN`: DSN PostgreSQL/TimescaleDB.
   - `CP_REDIS_URL`: Redis connection string.
   - `CP_LOG_LEVEL`: `INFO`, `DEBUG`, `WARN`, `ERROR`.

4. Chạy backend API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 5556 --app-dir backend
   ```

5. Chạy worker:
   - Binance ingestor:
     ```bash
     python -m app.workers.binance_ingestor
     ```
   - Data saver:
     ```bash
     python -m app.workers.data_saver
     ```
   - Gap fill worker:
     ```bash
     python -m app.workers.gap_fill_worker
     ```

## Thiết lập frontend
1. Chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```

2. Cài đặt phụ thuộc:
   ```bash
   npm install
   ```

3. Chạy dev server:
   ```bash
   npm run dev
   ```

4. Mở ứng dụng:
   - `http://localhost:5555`

## Thiết lập Docker runtime
1. Tại thư mục gốc repository:
   ```bash
   cd deploy/docker
   docker compose -f docker-compose.runtime.yml up -d --build
   ```

2. Kiểm tra trạng thái:
   ```bash
   docker compose -f docker-compose.runtime.yml ps
   docker compose -f docker-compose.runtime.yml logs --tail=50 backend
   ```

3. Dừng runtime:
   ```bash
   docker compose -f docker-compose.runtime.yml down
   ```

## Thiết lập Kubernetes baseline
1. Tạo secret PostgreSQL DSN:
   ```bash
   kubectl create secret generic crypto-backend-secrets --from-literal=postgres_dsn='postgresql://postgres:postgres@timescaledb:5432/binance_market'
   ```

2. Deploy manifest backend:
   ```bash
   kubectl apply -f deploy/k8s/backend-deployment.yaml
   ```

## Cấu hình hệ thống
Các giá trị cấu hình chính nằm trong `backend/app/core/config.py`. Đa số có thể được override bằng biến môi trường tiền tố `CP_`.

Các biến chính:
- `CP_POSTGRES_DSN`
- `CP_REDIS_URL`
- `CP_LOG_LEVEL`
- `CP_BINANCE_WS_BASE_URL`
- `CP_BINANCE_REST_BASE_URL`
- `CP_BINANCE_SYMBOLS`
- `CP_BINANCE_INTERVALS`

## Kiểm tra cơ bản
- Backend API:
  - `curl http://localhost:5556/healthz`
  - `curl http://localhost:5556/readyz`
  - `curl http://localhost:5556/metrics`
- Frontend:
  - `http://localhost:5555`
- REST sample:
  - `curl "http://localhost:5556/api/v1/market/klines?symbol=btcusdt&interval=1m&limit=10"`
