# Deployment

## Docker Compose runtime
Runtime stack được định nghĩa tại `deploy/docker/docker-compose.runtime.yml`.

### Các service chính
- `redis`: Redis Pub/Sub.
- `timescaledb`: TimescaleDB/PostgreSQL.
- `backend`: FastAPI API và WebSocket gateway.
- `ingestor`: Binance ingest worker.
- `data_saver`: Worker ghi candle vào DB.
- `gap_fill`: Worker phục hồi gap.
- `prometheus`: Metrics scraping.

### Khởi động
```bash
cd deploy/docker
docker compose -f docker-compose.runtime.yml up -d --build
```

### Kiểm tra
```bash
docker compose -f docker-compose.runtime.yml ps
docker compose -f docker-compose.runtime.yml logs --tail=100 backend
```

### Dừng
```bash
docker compose -f docker-compose.runtime.yml down
```

## Kubernetes baseline
Manifest backend nằm ở `deploy/k8s/backend-deployment.yaml`.

### Yêu cầu
- Secret `crypto-backend-secrets` chứa `postgres_dsn`.
- Redis service phải tồn tại và được truy cập qua `redis://redis:6379/0`.

### Deploy
```bash
kubectl apply -f deploy/k8s/backend-deployment.yaml
```

### Kiểm tra
```bash
kubectl get deployments
kubectl get pods -l app=crypto-backend
kubectl describe pod <pod-name>
```

## Ports mặc định
- Backend API: `5556`
- Frontend dev: `5555`
- Prometheus: `5557`

## Environment variables
Backend runtime dùng biến tiền tố `CP_`:
- `CP_POSTGRES_DSN`
- `CP_REDIS_URL`
- `CP_LOG_LEVEL`
- `CP_BINANCE_WS_BASE_URL`
- `CP_BINANCE_REST_BASE_URL`
- `CP_BINANCE_SYMBOLS`
- `CP_BINANCE_INTERVALS`
- `CP_RECONNECT_MAX_SECONDS`
- `CP_ENABLE_GAP_DETECTION`

## Runtime health
### Backend
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`

### Prometheus
- `http://localhost:5557`

## Ghi chú
- Docker Compose hiện tại không chứa frontend.
- Kubernetes manifest chỉ là backend baseline, cần bổ sung Redis/TimescaleDB/Secrets khi dùng production.
- `deploy/docker/docker-compose.runtime.yml` có `depends_on` để đảm bảo Redis và TimescaleDB sẵn sàng trước backend.
