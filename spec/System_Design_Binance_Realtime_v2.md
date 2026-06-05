# TÀI LIỆU THIẾT KẾ KIẾN TRÚC VÀ KỸ THUẬT HỆ THỐNG (SYSTEM DESIGN) V2
## DỰ ÁN: BINANCE REAL-TIME MARKET DATA & CANDLESTICK TRACKER
**Ngôn ngữ Backend:** Python (Asyncio, FastAPI, Redis, asyncpg)
**Cơ sở dữ liệu:** TimescaleDB (PostgreSQL) - Tối ưu chuỗi thời gian (Time-Series)
**Vai trò:** Kiến trúc sư hệ thống (System Architect)

---

### 1. KIẾN TRÚC TỔNG THỂ CẬP NHẬT (HIGH-LEVEL ARCHITECTURE)

Hệ thống được thiết kế theo mô hình **Kiến trúc hướng sự kiện (Event-Driven Architecture)** tách biệt hoàn toàn giữa tác vụ thu thập dữ liệu (I/O Bound), phân phối dữ liệu cho người dùng (Gateway) và lưu trữ dữ liệu vĩnh viễn (Persistence).

#### Các thành phần cốt lõi:
1. **Binance Fetcher Service (Worker):** Lắng nghe dữ liệu WebSocket từ Binance và đẩy vào Redis Pub/Sub.
2. **Message Broker (Redis Pub/Sub):** Xương sống truyền dẫn thông tin tốc độ cao.
3. **Data Saver Service (Database Worker):** Lắng nghe Redis, gom nhóm (Batching) các sự kiện đóng nến (`x: true`) và ghi vào Database để phục vụ lịch sử.
4. **API Gateway (FastAPI):**
   - **REST API:** Cung cấp endpoint lấy dữ liệu nến lịch sử (Historical Data).
   - **WebSocket API:** Phân phát dữ liệu Real-time xuống Client.
5. **Database (TimescaleDB):** Lưu trữ metadata và dữ liệu Klines (chuỗi thời gian), thiết kế sẵn sàng mở rộng cho Indicator (RSI, MACD...).

---

### 2. THIẾT KẾ CƠ SỞ DỮ LIỆU (DATABASE SCHEMA DESIGN)

Sử dụng **TimescaleDB** (dựa trên PostgreSQL) vì nó tối ưu tốc độ đọc/ghi cho Time-series data và hỗ trợ SQL nguyên bản. Thiết kế này tuân thủ nguyên tắc mở rộng: chia thành bảng Metadata (Relational) và bảng Dữ liệu chuỗi thời gian (Hypertable).

#### 2.1. Bảng Relational (Metadata)
* **Bảng `symbols` (Cặp giao dịch):**
  - `id` (SERIAL PRIMARY KEY)
  - `symbol` (VARCHAR(20) UNIQUE) - VD: "btcusdt"
  - `base_asset` (VARCHAR(10)) - VD: "btc"
  - `quote_asset` (VARCHAR(10)) - VD: "usdt"

* **Bảng `intervals` (Khung thời gian):**
  - `id` (SERIAL PRIMARY KEY)
  - `interval` (VARCHAR(5) UNIQUE) - VD: "1m", "5m", "1h"

* **Bảng `indicators` (Sẵn sàng mở rộng cho thuật toán tương lai):**
  - `id` (SERIAL PRIMARY KEY)
  - `code` (VARCHAR(20) UNIQUE) - VD: "RSI_14", "MACD_12_26_9"
  - `params` (JSONB) - Lưu tham số động của thuật toán.

#### 2.2. Bảng Hypertable (Time-Series Data)
Đây là các bảng được TimescaleDB tự động phân mảnh (partitioning) theo thời gian, giúp query hàng triệu records cực nhanh.

* **Bảng `klines` (Dữ liệu Nến):**
  - `timestamp` (TIMESTAMPTZ NOT NULL) - Bắt buộc làm Partition Key.
  - `symbol_id` (INT FOREIGN KEY)
  - `interval_id` (INT FOREIGN KEY)
  - `open` (DOUBLE PRECISION)
  - `high` (DOUBLE PRECISION)
  - `low` (DOUBLE PRECISION)
  - `close` (DOUBLE PRECISION)
  - `volume` (DOUBLE PRECISION)
  - *Chỉ mục (Index):* Composite Index trên `(symbol_id, interval_id, timestamp DESC)`.

* **Bảng `indicator_values` (Thiết kế mở rộng lưu số liệu tính toán):**
  - `timestamp` (TIMESTAMPTZ NOT NULL)
  - `symbol_id` (INT FOREIGN KEY)
  - `interval_id` (INT FOREIGN KEY)
  - `indicator_id` (INT FOREIGN KEY)
  - `values` (JSONB) - Dùng JSONB để lưu giá trị linh hoạt. (VD: RSI chỉ có 1 giá trị `{"value": 45.5}`, nhưng MACD sẽ có `{"macd": 1.2, "signal": 0.8, "hist": 0.4}`).

---

### 3. CHIẾN LƯỢC TẢI DỮ LIỆU HYBRID (HYBRID DATA LOADING)

Sự kết hợp giữa REST API (Lấy dữ liệu lớn một lần) và WebSocket (Nhận dữ liệu nhỏ liên tục) là chuẩn mực (Standard pattern) của các sàn giao dịch hiện nay.

**Quy trình chuẩn tại Frontend:**
1. **Khởi tạo (Bootstrap):** Người dùng mở trang web cặp `BTCUSDT` khung `1m`. UI ngay lập tức gọi HTTP GET `GET /api/v1/market/klines?symbol=btcusdt&interval=1m&limit=1000`.
2. **Vẽ nền móng:** Nhận về mảng JSON chứa 1000 nến, đưa vào thư viện `TradingView Lightweight Charts` qua hàm `series.setData(historicalData)`.
3. **Chuyển giao (Hand-off):** UI mở luồng WebSocket kết nối đến `wss://domain.com/ws/market`.
4. **Cập nhật mượt mà (Real-time Merge):** Nhận từng gói tin JSON tick giá hoặc đóng nến từ WebSocket, nhúng trực tiếp vào đồ thị qua hàm `series.update(liveData)`.

---

### 4. CÀI ĐẶT BẰNG PYTHON CẬP NHẬT (CODE THÊM DATA SAVER & REST API)

#### 4.1. Data Saver Worker (Lắng nghe Redis và Ghi Batch vào Database)
Để không làm chậm luồng bắn real-time, việc lưu database được tách ra thành một tiến trình riêng.
```python
import asyncio
import json
import asyncpg
import redis.asyncio as aioredis

REDIS_URL = "redis://localhost:6379/0"
DB_DSN = "postgres://user:pass@localhost:5432/binance_market"

class DataSaverWorker:
    def __init__(self):
        self.batch_data = []
        self.batch_size = 100 # Gom đủ 100 nến hoặc lưu sau mỗi 2 giây

    async def connect(self):
        self.redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        await self.pubsub.psubscribe("market:kline:*")
        
        # Connection Pool siêu tốc cho PostgreSQL
        self.db_pool = await asyncpg.create_pool(dsn=DB_DSN)

    async def flush_to_db(self):
        if not self.batch_data:
            return
        
        data_to_insert = self.batch_data.copy()
        self.batch_data.clear()

        # Thực thi BULK INSERT
        query = """
        INSERT INTO klines (timestamp, symbol_id, interval_id, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT DO NOTHING
        """
        async with self.db_pool.acquire() as conn:
            # Map symbol và interval sang ID trước khi insert (trong thực tế dùng cache in-memory)
            await conn.executemany(query, data_to_insert)

    async def listen_and_batch(self):
        async for message in self.pubsub.listen():
            if message["type"] == "pmessage":
                data = json.loads(message["data"])
                # Chỉ lưu khi nến đã chính thức đóng (is_closed: True)
                if data.get("is_closed"): 
                    record = (
                        data["end_time"], 1, 1, # Dummy IDs for symbol/interval
                        float(data["open"]), float(data["high"]),
                        float(data["low"]), float(data["close"]), float(data["volume"])
                    )
                    self.batch_data.append(record)

            if len(self.batch_data) >= self.batch_size:
                await self.flush_to_db()

    async def periodic_flush(self):
        # Đảm bảo flush dữ liệu nếu không đủ batch_size nhưng hết thời gian chờ
        while True:
            await asyncio.sleep(2)
            await self.flush_to_db()
```

#### 4.2. Bổ sung REST API vào `server_gateway.py` (FastAPI)
Bổ sung Endpoint API để Frontend gọi ở bước 1 của chiến lược Hybrid.
```python
from fastapi import FastAPI, Depends
import asyncpg

@app.get("/api/v1/market/klines")
async def get_historical_klines(symbol: str, interval: str, limit: int = 1000):
    # Lấy dữ liệu siêu tốc từ TimescaleDB Hypertable
    query = """
        SELECT timestamp, open, high, low, close, volume 
        FROM klines k
        JOIN symbols s ON k.symbol_id = s.id
        JOIN intervals i ON k.interval_id = i.id
        WHERE s.symbol = $1 AND i.interval = $2
        ORDER BY timestamp DESC
        LIMIT $3
    """
    async with app.state.db_pool.acquire() as conn:
        rows = await conn.fetch(query, symbol.lower(), interval.lower(), limit)
        
    # Sắp xếp lại theo thời gian tăng dần để Frontend vẽ từ trái sang phải
    result = [dict(row) for row in reversed(rows)]
    return {"status": "success", "data": result}
```

---

### 5. TỐI ƯU HÓA BỔ SUNG: MỞ RỘNG TÍNH TOÁN INDICATOR

Khi đã có cấu trúc CSDL bền vững với Time-Series, để tính toán MACD hay RSI real-time, ta chỉ cần:
1. Thêm một `Indicator Worker` độc lập.
2. Worker này cũng subscribe vào Redis channel `market:kline:*`.
3. Khi nhận tín hiệu đóng nến, nó gọi hàm tính toán nội bộ (sử dụng thư viện `TA-Lib` hoặc Pandas), ví dụ: `RSI = compute_rsi(new_candle, historical_db_candles)`.
4. Ghi đè vào bảng `indicator_values` dạng JSONB: `{"rsi": 65.4}`.
5. Bắn tiếp kết quả này vào Redis `market:indicator:rsi:1m:btcusdt` để đẩy lên Gateway Server và hiển thị trực tiếp lên Frontend cho user.
