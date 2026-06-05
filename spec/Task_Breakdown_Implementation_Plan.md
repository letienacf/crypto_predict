# TASK BREAKDOWN TRIỂN KHAI HỆ THỐNG BINANCE REALTIME (TEAM-BASED)

## 1) Mục tiêu tài liệu
- Chia việc theo team để có thể làm độc lập, giảm phụ thuộc chéo.
- Mỗi task có yêu cầu rõ ràng, Input (Income) và Output (Outcome).
- Chuẩn hóa coding convention theo từng ngôn ngữ.
- Đảm bảo mở rộng, dễ bảo trì, tuân thủ SOLID.
- Bắt buộc Null-Safety, Crash-Safety, Memory-Safety, Thread-Safety.

## 2) Kiến trúc chia team độc lập
- Team A: Market Data Ingestion (Binance WS + reconnect + gap detection).
- Team B: Streaming & Event Contract (Redis channels, event schema, versioning).
- Team C: Persistence (TimescaleDB schema, write worker, historical query).
- Team D: API Gateway (WebSocket fanout + REST historical API).
- Team E: Frontend Realtime UI (Watchlist, chart, live candle stats).
- Team F: SRE/DevOps/Observability (CI/CD, monitoring, alerting, runbook).
- Team G: QA/Performance/Resilience (test tự động, latency test, chaos test).

Nguyên tắc tách độc lập:
- Mọi team tích hợp qua hợp đồng dữ liệu (contract-first) và interface rõ ràng.
- Không truy cập trực tiếp DB/service nội bộ của team khác nếu chưa qua API/contract.
- Thay đổi breaking change bắt buộc tăng version contract.

---

## 3) Backlog chi tiết theo team

## Team A - Market Data Ingestion

### A1. Binance WebSocket Connection Manager
- Yêu cầu:
  - Kết nối các stream aggTrade + kline cho danh sách symbol active.
  - Tự reconnect theo exponential backoff + jitter.
  - Rotate kết nối trước 5 phút khi đạt ngưỡng 24h.
- Input (Income):
  - Danh sách symbol active từ config/service.
  - Danh sách interval bắt buộc: 1m, 5m, 15m, 1h, 4h, 1d, 1w.
- Output (Outcome):
  - Luồng message chuẩn hóa gửi sang Team B.
  - Metric kết nối (connected, reconnect_count, downtime_seconds).
- Điều kiện hoàn thành:
  - Không mất stream quá 3 giây trong test reconnect.
  - Có integration test mô phỏng disconnect.

### A2. Kline Close Detector (x=true)
- Yêu cầu:
  - Bắt chính xác sự kiện đóng nến (x=true), bỏ nhiễu duplicate.
  - Chuẩn hóa payload OHLCV + open_time + close_time.
- Input (Income):
  - Kline raw payload từ Binance.
- Output (Outcome):
  - Sự kiện kline.closed chuẩn contract v1.
- Điều kiện hoàn thành:
  - So khớp close price 100% với Binance reference trong test replay.

### A3. Gap Detector + Recovery Trigger
- Yêu cầu:
  - Phát hiện khoảng trống dữ liệu theo symbol-interval-time window.
  - Phát trigger để Team C gọi REST backfill.
- Input (Income):
  - Timeline sự kiện ingest thực tế.
- Output (Outcome):
  - Gap event chứa from_ts, to_ts, symbol, interval.
- Điều kiện hoàn thành:
  - Mất mạng 30s vẫn phát hiện đúng gap trong vòng 2s sau reconnect.

---

## Team B - Streaming & Event Contract

### B1. Event Schema Registry (v1)
- Yêu cầu:
  - Định nghĩa schema chuẩn cho trade.tick, kline.partial, kline.closed, system.gap_detected.
  - Có quy tắc versioning (backward-compatible trước, breaking change tăng major).
- Input (Income):
  - Yêu cầu dữ liệu từ Team A/C/D/E.
- Output (Outcome):
  - Bộ schema JSON + tài liệu contract + ví dụ payload.
- Điều kiện hoàn thành:
  - Các team pass contract test bằng validator chung.

### B2. Redis Channel Naming + Pub/Sub Gateway
- Yêu cầu:
  - Quy ước channel rõ ràng: market:{event}:{symbol}:{interval}.
  - Tách channel nóng (tick) và channel trọng yếu (kline.closed).
- Input (Income):
  - Sự kiện chuẩn hóa từ Team A.
- Output (Outcome):
  - Kênh pub/sub ổn định cho Team C/D subscribe.
- Điều kiện hoàn thành:
  - Throughput test đạt mức tải mục tiêu mà không drop message nội bộ.

### B3. Backpressure & Queue Guard
- Yêu cầu:
  - Không để queue/buffer tăng vô hạn.
  - Có chiến lược drop policy cho event không trọng yếu (tick quá dày).
- Input (Income):
  - Luồng tick burst cao.
- Output (Outcome):
  - Hệ thống không OOM trong stress test.
- Điều kiện hoàn thành:
  - Memory usage ổn định trong soak test >= 2h.

---

## Team C - Persistence (TimescaleDB)

### C1. DB Migration & Hypertable Setup
- Yêu cầu:
  - Tạo bảng symbols, intervals, klines, indicator_values.
  - Tạo hypertable + index composite đúng thiết kế.
- Input (Income):
  - SQL schema thiết kế v2.
- Output (Outcome):
  - Bộ migration idempotent cho dev/staging/prod.
- Điều kiện hoàn thành:
  - Có migration rollback/test migration CI.

### C2. Data Saver Worker (Batch Insert)
- Yêu cầu:
  - Subscribe kline.closed từ Team B, batch insert theo kích thước + timeout.
  - Idempotent insert (ON CONFLICT DO NOTHING / upsert phù hợp).
- Input (Income):
  - Event kline.closed chuẩn v1.
- Output (Outcome):
  - Dữ liệu nến lưu bền vững, không trùng.
- Điều kiện hoàn thành:
  - Không mất dữ liệu trong test burst + restart worker.

### C3. Gap Fill Worker (Binance REST /api/v3/klines)
- Yêu cầu:
  - Khi nhận gap event, gọi REST backfill và patch DB.
  - Gắn cờ nguồn dữ liệu (recovered/live) để audit.
- Input (Income):
  - Gap event từ Team A/B.
- Output (Outcome):
  - Vùng dữ liệu thiếu được lấp đầy và đồng bộ lại cho Gateway.
- Điều kiện hoàn thành:
  - Không còn missing candle sau kịch bản mất mạng 30s.

### C4. Historical Query Service
- Yêu cầu:
  - Query historical nến theo symbol + interval + limit.
  - Trả dữ liệu tăng dần theo thời gian để frontend setData trực tiếp.
- Input (Income):
  - Request từ Team D REST API.
- Output (Outcome):
  - Dataset ổn định, latency query đạt SLA.
- Điều kiện hoàn thành:
  - P95 query < 120ms với limit=1000 trên dữ liệu benchmark.

---

## Team D - API Gateway

### D1. WebSocket Gateway Fanout
- Yêu cầu:
  - Quản lý kết nối client lớn, subscribe theo symbol/interval.
  - Broadcast event từ Redis ra đúng nhóm client.
- Input (Income):
  - Event stream từ Team B.
- Output (Outcome):
  - Client nhận tick + kline.closed theo đúng kênh quan tâm.
- Điều kiện hoàn thành:
  - Benchmark 10,000 connection với latency đúng NFR.

### D2. REST API Historical Endpoint
- Yêu cầu:
  - Cung cấp GET /api/v1/market/klines với validation chặt.
  - Chống input lỗi: symbol rỗng, interval sai, limit vượt ngưỡng.
- Input (Income):
  - HTTP request frontend.
- Output (Outcome):
  - JSON response chuẩn contract + mã lỗi rõ ràng.
- Điều kiện hoàn thành:
  - OpenAPI đầy đủ + contract test pass.

### D3. Watchlist Session Management
- Yêu cầu:
  - Theo dõi watchlist theo user/session và cập nhật subscribe động.
  - Giải phóng tài nguyên khi client disconnect.
- Input (Income):
  - User actions từ frontend.
- Output (Outcome):
  - Luồng dữ liệu đúng watchlist, không rò rỉ subscription.
- Điều kiện hoàn thành:
  - Không còn dangling subscription sau 1,000 lần connect/disconnect.

---

## Team E - Frontend Realtime UI

### E1. Bootstrap Hybrid Load (REST + WS)
- Yêu cầu:
  - Fetch 1000 nến bằng REST, sau đó handoff sang WS update.
  - Không re-render toàn app theo từng tick.
- Input (Income):
  - REST historical data + WS live data từ Team D.
- Output (Outcome):
  - Chart hiển thị liên tục, mượt, không giật.
- Điều kiện hoàn thành:
  - FPS ổn định, không lag rõ rệt khi tick dày.

### E2. Chart & Candle Close Rendering
- Yêu cầu:
  - Tích hợp TradingView Lightweight Charts.
  - Khi kline.closed đến, nến cũ phải chốt cố định và mở nến mới đúng thời điểm.
- Input (Income):
  - Event kline.partial / kline.closed.
- Output (Outcome):
  - Biểu đồ phản ánh đúng OHLCV Binance.
- Điều kiện hoàn thành:
  - AC chốt nến chính xác đạt 100% trong test đối chiếu.

### E3. Watchlist + Price Flash Effect
- Yêu cầu:
  - Giá nhảy realtime, màu tăng/giảm + flash 150ms.
  - Tối ưu render từng row (virtualization/memo hóa khi cần).
- Input (Income):
  - Tick stream theo symbol.
- Output (Outcome):
  - Watchlist phản hồi tức thời, không mỏi mắt.
- Điều kiện hoàn thành:
  - UI phản hồi < 100ms từ lúc nhận message ở browser.

### E4. Live Candle Stats + Countdown
- Yêu cầu:
  - Hiển thị O/H/L/C/V của nến hiện tại + countdown chính xác.
  - Countdown đồng bộ server time (không lệch do local clock).
- Input (Income):
  - Live kline + server timestamp sync.
- Output (Outcome):
  - Trader nhìn rõ thời gian đóng nến còn lại.
- Điều kiện hoàn thành:
  - Sai lệch countdown < 1s trong 1h chạy liên tục.

---

## Team F - SRE/DevOps/Observability

### F1. CI/CD + Quality Gates
- Yêu cầu:
  - Pipeline lint, test, security scan, build image, deploy.
  - Block merge nếu coverage/quality dưới ngưỡng.
- Input (Income):
  - Source code từ các team.
- Output (Outcome):
  - Quy trình release ổn định, rollback nhanh.
- Điều kiện hoàn thành:
  - Mọi service deploy tự động staging và có release tag.

### F2. Monitoring & Alerting
- Yêu cầu:
  - Dashboard: ingest lag, ws reconnect, queue depth, p95 latency, error rate.
  - Alert khi mất stream, memory tăng bất thường, crash loop.
- Input (Income):
  - Metrics/log/traces từ toàn hệ thống.
- Output (Outcome):
  - Cảnh báo sớm trước khi ảnh hưởng user.
- Điều kiện hoàn thành:
  - Có runbook cho mỗi loại alert quan trọng.

### F3. Runtime Hardening
- Yêu cầu:
  - Healthcheck/readiness/liveness cho từng service.
  - Giới hạn memory/cpu container + restart policy.
- Input (Income):
  - Deployment manifest + runtime config.
- Output (Outcome):
  - Hệ thống tự phục hồi khi lỗi cục bộ.
- Điều kiện hoàn thành:
  - Chaos test service restart không làm ngắt toàn hệ thống.

---

## Team G - QA/Performance/Resilience

### G1. Contract Test Suite
- Yêu cầu:
  - Kiểm tra schema event và API response cho mọi version đang hỗ trợ.
- Input (Income):
  - Contract từ Team B/D.
- Output (Outcome):
  - Báo cáo pass/fail theo từng endpoint/event.
- Điều kiện hoàn thành:
  - Không còn mismatch schema giữa team.

### G2. Latency E2E Test
- Yêu cầu:
  - Đo thời gian Binance event -> backend -> browser render.
  - So sánh với mục tiêu < 300ms, lý tưởng < 150ms.
- Input (Income):
  - Môi trường test + dữ liệu mô phỏng.
- Output (Outcome):
  - Báo cáo p50/p95/p99 latency và điểm nghẽn.
- Điều kiện hoàn thành:
  - Có dashboard xu hướng latency theo build.

### G3. Failover + Gap Fill Validation
- Yêu cầu:
  - Mô phỏng ngắt mạng worker, kill process, reconnect.
  - Xác nhận dữ liệu không gap sau recovery.
- Input (Income):
  - Kịch bản chaos và oracle dữ liệu tham chiếu.
- Output (Outcome):
  - Biên bản chứng minh cơ chế tự phục hồi hoạt động.
- Điều kiện hoàn thành:
  - Pass AC khôi phục sau sự cố trong PRD.

---

## 4) Chuẩn coding convention theo ngôn ngữ

## 4.1 Python (Backend/Worker/FastAPI)
- Naming:
  - module/file: snake_case.
  - class: PascalCase.
  - function/variable: snake_case.
  - constant: UPPER_SNAKE_CASE.
  - private member: prefix _name.
- Typing:
  - Bắt buộc type hints cho public function/method.
  - Dùng Optional[T] rõ ràng thay vì ngầm định None.
- Structure:
  - Tách layer: api, service, repository, domain, infrastructure.
  - Không để handler gọi DB trực tiếp nếu có service/repository.
- Style:
  - PEP 8, Black, isort, Ruff.
  - Docstring ngắn cho public API (Google style hoặc NumPy style, thống nhất một chuẩn).

## 4.2 TypeScript/React (Frontend)
- Naming:
  - component/class/type/interface: PascalCase.
  - function/variable/hook: camelCase (hook bắt đầu bằng use).
  - constant: UPPER_SNAKE_CASE.
  - file component: PascalCase.tsx; file utility: camelCase.ts.
- Structure:
  - Tách rõ: features, shared, services(api/ws), store, ui.
  - Không trộn logic WS nặng vào component render.
- Style:
  - ESLint + Prettier + TypeScript strict mode.
  - Tránh any; nếu bất khả kháng phải TODO + lý do.

## 4.3 SQL (PostgreSQL/TimescaleDB)
- Naming:
  - table/column/index: snake_case.
  - primary key: id.
  - foreign key: {table_singular}_id.
- Query:
  - Không SELECT * trong production query.
  - Mọi query cần index strategy và explain plan cho query nóng.
- Migration:
  - Mỗi migration phải có forward + rollback tương ứng.

## 4.4 Redis Channel/Event Naming
- Channel format chuẩn:
  - market:trade.tick:{symbol}
  - market:kline.partial:{symbol}:{interval}
  - market:kline.closed:{symbol}:{interval}
  - system:gap_detected:{symbol}:{interval}
- Symbol/interval chuẩn hóa lowercase.

## 4.5 YAML/DevOps
- key dùng lowercase_snake_case hoặc lowercase-kebab-case, thống nhất trong repo.
- Mọi manifest phải có resource requests/limits, healthcheck, restart policy.
- Secret tuyệt đối không hardcode vào repo.

---

## 5) SOLID áp dụng bắt buộc

- S (Single Responsibility):
  - Mỗi class/service chỉ có 1 lý do để thay đổi.
  - Ví dụ: WebSocket ingest không kiêm nhiệm ghi DB.
- O (Open/Closed):
  - Mở rộng qua interface/strategy thay vì sửa code lõi.
  - Ví dụ: thêm indicator mới bằng plugin worker.
- L (Liskov Substitution):
  - Interface implementation thay thế được mà không phá hành vi.
- I (Interface Segregation):
  - Interface nhỏ, chuyên biệt theo use-case.
  - Tránh interface lớn ép class implement dư thừa.
- D (Dependency Inversion):
  - Layer cao phụ thuộc abstraction, không phụ thuộc concrete.
  - Dùng DI container/factory cho client DB, Redis, Binance.

Checklist review SOLID cho mỗi PR:
- Class mới có đang làm quá nhiều việc không?
- Có hardcode dependency hạ tầng trong domain/service không?
- Thêm tính năng mới có phải sửa nhiều module cũ không?

---

## 6) Null-Safety, Crash-Safety, Memory-Safety, Thread-Safety (bắt buộc)

## 6.1 Null-Safety
- Validate input tại biên (API, WS message, env config).
- Không truy cập field trước khi kiểm tra tồn tại/kiểu dữ liệu.
- Dùng schema validator (Pydantic/Zod) cho payload vào-ra.
- Mọi Optional phải có nhánh xử lý rõ ràng.

## 6.2 Crash-Safety
- Bọc lỗi theo tầng:
  - tầng infra: retry có kiểm soát + circuit breaker.
  - tầng API: trả mã lỗi chuẩn, không lộ stacktrace nội bộ.
- Không để exception chưa bắt thoát khỏi loop xử lý realtime.
- Có dead-letter/log channel cho event lỗi parse.

## 6.3 Memory-Safety
- Cấm buffer/list không giới hạn.
- Batch queue phải có max size + policy khi quá tải.
- Đóng kết nối, release resource trong shutdown hook.
- Frontend phải unsubscribe WS/listener khi unmount để tránh memory leak.

## 6.4 Thread-Safety / Concurrency-Safety
- Trạng thái dùng chung phải qua cơ chế đồng bộ (asyncio.Lock hoặc actor model).
- Tránh mutate shared state từ nhiều coroutine/thread cùng lúc.
- Idempotency key cho luồng có khả năng nhận duplicate event.
- Viết test race condition cho watchlist subscribe/unsubscribe.

---

## 7) Định nghĩa hoàn thành chung (Global DoD)
- Pass unit test + integration test + contract test.
- Không có lỗi lint/type-check mức blocker.
- Có logging, metrics, tracing cho flow chính.
- Có tài liệu vận hành ngắn cho service mới.
- Đáp ứng mục tiêu latency và độ bền theo PRD.

## 8) Mốc triển khai đề xuất (6 sprint)
- Sprint 1: B1, C1, D2 skeleton, E1 skeleton, F1.
- Sprint 2: A1, A2, B2, D1.
- Sprint 3: C2, E2, E3, G1.
- Sprint 4: A3, C3, D3, E4.
- Sprint 5: F2, F3, G2.
- Sprint 6: G3, hardening, performance tuning, release candidate.

## 9) Ma trận phụ thuộc tối thiểu
- Team A phụ thuộc B1 (schema).
- Team C phụ thuộc B1/B2.
- Team D phụ thuộc B2 và C4.
- Team E phụ thuộc D1/D2 contract ổn định.
- Team G phụ thuộc artifacts test từ tất cả team.

Với ma trận này, các team vẫn có thể phát triển song song bằng mock contract ngay từ Sprint 1.
