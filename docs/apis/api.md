# API

## REST API
Tất cả endpoint REST nằm dưới tiền tố `/api/v1`.

### GET /api/v1/market/klines
Lấy dữ liệu candles lịch sử.

#### Query parameters
- `symbol` (string, required): mã cặp tiền tệ, các ký tự thường, số, không dấu, ví dụ `btcusdt`.
- `interval` (string, required): một trong các giá trị sau:
  - `1m`, `5m`, `15m`, `1h`, `4h`, `1d`, `1w`
- `limit` (integer, optional, default 1000): số lượng candles cần trả về, giá trị từ `1` đến `5000`.

#### Response
- `status`: luôn là `success`.
- `data`: danh sách candle theo thứ tự thời gian tăng dần.

#### Ví dụ
```bash
curl "http://localhost:5556/api/v1/market/klines?symbol=btcusdt&interval=1m&limit=10"
```

#### Response mẫu
```json
{
  "status": "success",
  "data": [
    {
      "timestamp": "2026-01-01T00:00:00+00:00",
      "open": 44000.0,
      "high": 44100.0,
      "low": 43950.0,
      "close": 44050.0,
      "volume": 12.3
    }
  ]
}
```

## System endpoints
### GET /healthz
- Kiểm tra dịch vụ backend đang chạy.
- Response:
  - `200 OK` với `{"status": "ok"}`.

### GET /readyz
- Kiểm tra backend đã sẵn sàng nhận traffic.
- Phụ thuộc gateway Redis.
- Response:
  - `200 OK` khi sẵn sàng.
  - `503 Service Unavailable` khi chưa sẵn sàng.

### GET /api/v1/system/time
- Trả về thời gian server hiện tại.
- Response mẫu:
```json
{ "server_time": "2026-01-01T12:34:56+00:00" }
```

### GET /metrics
- Trả về metrics Prometheus.
- Dùng để scrape bởi Prometheus.

## WebSocket API
Endpoint WebSocket:
- `ws://localhost:5556/ws/market`

### Kết nối
Tham số query string:
- `symbols`: danh sách symbol nối bằng dấu phẩy, ví dụ `btcusdt,ethusdt`.
- `intervals`: danh sách interval nối bằng dấu phẩy, ví dụ `1m,5m`.

Ví dụ kết nối:
```js
const ws = new WebSocket("ws://localhost:5556/ws/market?symbols=btcusdt,ethusdt&intervals=1m,5m");
```

### Cập nhật watchlist runtime
Client có thể gửi message JSON với action `set_watchlist`:
```json
{
  "action": "set_watchlist",
  "symbols": ["btcusdt", "ethusdt"],
  "intervals": ["1m", "5m"]
}
```

Sau khi nhận, server trả về:
```json
{
  "event_type": "watchlist.updated",
  "symbols": ["btcusdt", "ethusdt"],
  "intervals": ["1m", "5m"]
}
```

### Payload sự kiện WebSocket
Gateway phát tới client payload JSON từ Redis event bus. Thông thường payload chứa ít nhất:
- `event_type`
- `symbol`
- `interval`
- `ingested_at`

Ví dụ `kline.closed` hoặc `kline.partial` sẽ có dữ liệu candle chi tiết.

### Lọc client
- Nếu client chỉ định `symbols`, chỉ nhận event với symbol tương ứng.
- Nếu client chỉ định `intervals`, chỉ nhận event với interval tương ứng.

## Lỗi phổ biến
- `422 Unprocessable Entity`: tham số query `symbol`, `interval` hoặc `limit` không hợp lệ.
- `503 Service Unavailable` tại `/readyz`: backend chưa kết nối Redis.

## Ghi chú
- REST API ưu tiên trả dữ liệu từ DB.
- Nếu DB trống hoặc lỗi, API fallback sang Binance REST để lấy candle và seed lại DB.
- Interval và symbol được chuẩn hóa sang chữ thường với `symbol` chỉ hỗ trợ alphanumeric.
