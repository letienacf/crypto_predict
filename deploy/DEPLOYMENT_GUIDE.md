# Deployment Guide

This guide documents the working deployment for the current repository state.
It matches the ports and services that are already configured in the workspace:

- Frontend: `5555`
- Backend API: `5556`
- Prometheus: `5557`
- Redis: `6379` inside the Docker network
- TimescaleDB/PostgreSQL: `5432` inside the Docker network

## 1. What is deployed

The runtime stack is split into two parts:

- Docker Compose runtime for backend services:
  - `redis`
  - `timescaledb`
  - `backend`
  - `ingestor`
  - `data_saver`
  - `gap_fill`
  - `prometheus`
- Local frontend development server:
  - Vite dev server on `http://localhost:5555`

This separation is intentional because the current Compose runtime does not package the frontend.

## 2. Prerequisites

You need:

- Docker Engine and Docker Compose v2
- Node.js 18+ for the frontend dev server
- Python 3.11+ if you want to run backend services outside Docker

Recommended versions in this workspace:

- Docker 29+
- Node 18.19+

## 3. Start the backend runtime stack

From the repository root, run:

```bash
cd deploy/docker
docker compose -f docker-compose.runtime.yml up -d --build
```

What this does:

- Builds the backend image from `backend/Dockerfile`
- Starts Redis and TimescaleDB
- Starts the FastAPI backend on `5556`
- Starts the Binance ingestor worker
- Starts the data saver worker
- Starts the gap fill worker
- Starts Prometheus on `5557`

### Expected result

After a successful startup, these services should be healthy or running:

- `redis`: healthy
- `timescaledb`: healthy
- `backend`: healthy
- `ingestor`: running
- `data_saver`: running
- `gap_fill`: running
- `prometheus`: running

### Useful checks

```bash
cd deploy/docker
docker compose -f docker-compose.runtime.yml ps
docker compose -f docker-compose.runtime.yml logs --tail=100 backend
```

## 4. Start the frontend

From the frontend folder:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at:

- `http://localhost:5555`

The frontend uses same-origin paths in dev, and Vite proxies them to the backend on `5556`.
The important browser-visible paths are:

- `/api/v1/...`
- `/ws/market`

## 5. Verify the system

### Backend health

```bash
curl http://localhost:5556/healthz
curl http://localhost:5556/readyz
curl http://localhost:5556/metrics
```

### Frontend availability

Open:

- `http://localhost:5555`

### Prometheus

Open:

- `http://localhost:5557`

### API sample

```bash
curl "http://localhost:5556/api/v1/market/klines?symbol=btcusdt&interval=1m&limit=10"
```

## 6. Stop the system

### Stop backend runtime

```bash
cd deploy/docker
docker compose -f docker-compose.runtime.yml down
```

### Stop frontend

Use `Ctrl+C` in the terminal where `npm run dev` is running.

## 7. Current port map

| Service | Port |
| --- | --- |
| Frontend Vite dev server | `5555` |
| Backend API | `5556` |
| Prometheus | `5557` |
| Redis | `6379` |
| TimescaleDB | `5432` |

## 8. Environment variables used by the runtime

Backend containers in Compose rely on:

- `CP_REDIS_URL=redis://redis:6379/0`
- `CP_POSTGRES_DSN=postgresql://postgres:postgres@timescaledb:5432/binance_market`
- `CP_LOG_LEVEL=INFO`

If you run the backend outside Docker, these defaults are also supported by the app settings.

## 9. Kubernetes baseline

The repository also contains a Kubernetes manifest:

- `deploy/k8s/backend-deployment.yaml`

That manifest mirrors the backend runtime on port `5556` and includes readiness, liveness, and startup probes.

It is a baseline deployment example, not the full cluster definition. You still need Redis, TimescaleDB, secrets, and the related services in your cluster.

## 10. Troubleshooting

### Backend container is unhealthy

- Check `docker compose logs backend`
- Confirm Redis and TimescaleDB are healthy first
- Verify port `5556` is free on the host

### Frontend cannot reach the API

- Confirm the backend is reachable at `http://localhost:5556`
- Confirm the frontend dev server has been restarted after `frontend/vite.config.ts` changes
- Confirm the frontend is using relative API and WebSocket paths in `frontend/src/api/marketApi.ts` and `frontend/src/services/marketWsClient.ts`

### Prometheus is not scraping

- Confirm the target in `ops/prometheus/prometheus.yml` points to `backend:5556`
- Confirm the backend container is healthy

### Vite warns about Node version

- The workspace currently runs on Node 18.19.
- The frontend dev server starts successfully, but some dev dependencies prefer Node 20+.
- If you upgrade Node, prefer Node 20 LTS or newer.

## 11. Current deployment status in this workspace

The runtime stack is already deployed in this workspace:

- backend API is healthy on `5556`
- Redis and TimescaleDB are healthy
- Prometheus is running on `5557`
- frontend dev server is running on `5555`
