# TÀI LIỆU ĐẶC TẢ YÊU CẦU SẢN PHẨM (PRD)
## DỰ ÁN: BINANCE REAL-TIME MARKET DATA & CANDLESTICK TRACKER

---

### 1. TỔNG QUAN DỰ ÁN (PROJECT OVERVIEW)
#### 1.1. Bối cảnh (Background)
Trong thị trường giao dịch tiền điện tử (Cryptocurrency), dữ liệu biến động giá theo thời gian thực (real-time) và khoảnh khắc đóng nến (candlestick closing) có vai trò sống còn đối với các nhà giao dịch (Traders) và các thuật toán giao dịch tự động (Trading Bots). Việc chậm trễ dù chỉ một vài mili-giây (ms) trong việc nhận diện nến đóng có thể dẫn đến việc vào lệnh sai lệch vị thế hoặc mất đi cơ hội đầu tư tối ưu.

#### 1.2. Mục tiêu sản phẩm (Product Goal)
Xây dựng một hệ thống backend hiệu năng cao, độ trễ cực thấp (Ultra Low-Latency) kết nối trực tiếp tới Binance để thu thập dữ liệu thị trường và đẩy tức thì về giao diện người dùng (UI). Hệ thống tập trung giải quyết hai bài toán cốt lõi:
1. Luồng cập nhật giá biến động liên tục (Tick-by-tick).
2. Phát hiện và xử lý sự kiện đóng nến ngay lập tức cho các khung thời gian: **1m, 5m, 15m, 1h, 4h, 1d, 1w** và đẩy dữ liệu OHLCV (Open, High, Low, Close, Volume) lên UI mà không có độ trễ nhận biết được bởi người dùng.

#### 1.3. Phạm vi sản phẩm (Scope)
* **Giai đoạn 1:** Hỗ trợ thị trường Spot (Giao ngay) cho danh sách 50 cặp tiền tệ phổ biến nhất (BTCUSDT, ETHUSDT, BNBUSDT,...).
* **Nền tảng:** Ứng dụng Web (Web Application) tối ưu hóa cho trình duyệt máy tính (Desktop) và thiết bị di động (Mobile).

---

### 2. ĐỐI TƯỢNG NGƯỜI DÙNG & CA SỬ DỤNG (USER PERSONAS & USE CASES)
* **Trader lướt sóng (Scalper):** Cần nhìn thấy giá nhảy liên tục để đặt lệnh thủ công trên UI. Theo dõi sát sao nến 1m và 5m để đưa ra quyết định trong vài giây.
* **Swing Trader / Day Trader:** Theo dõi các khung giờ lớn hơn (15m, 1h, 4h) để xác nhận xu hướng đồ thị khi đóng nến, từ đó kích hoạt chiến lược giao dịch trong ngày.

---

### 3. YÊU CẦU CHỨC NĂNG CHI TIẾT (DETAILED FUNCTIONAL REQUIREMENTS)

#### 3.1. Tính năng 1: Cập nhật giá Real-time (Tick-by-Tick Price Stream)
* **Mô tả:** Hệ thống hiển thị giá khớp lệnh gần nhất của các cặp tiền được chọn theo thời gian thực.
* **Luồng dữ liệu (Data Source):** Kết nối tới Binance WebSocket API qua `Aggregate Trade Streams` hoặc `Ticker Streams`.
* **Yêu cầu hành vi hệ thống:**
    * Ngay khi Binance phát sinh sự kiện khớp lệnh (`aggTrade`), Backend thu nhận payload, trích xuất giá hiện tại (`p` - price) và đẩy thẳng xuống client.
    * Giao diện UI cần cập nhật con số giá ngay lập tức.
    * **Hiệu ứng UI:** Nếu giá tăng so với tick trước đó, số giá đổi sang màu xanh lá (`#00b060`). Nếu giá giảm, đổi sang màu đỏ (`#ff3b30`). Hiệu ứng nhấp nháy (flash) nhẹ diễn ra trong vòng 150ms để không gây mỏi mắt cho người dùng.

#### 3.2. Tính năng 2: Phát hiện và xử lý Đóng nến Real-time (Candlestick Close Alert)
* **Mô tả:** Đây là tính năng cốt lõi. Hệ thống phải nhận biết chính xác thời điểm một cây nến của một khung giờ cụ thể kết thúc, chốt các thông số OHLCV và cập nhật lên UI ngay lập tức.
* **Các khung thời gian bắt buộc (Intervals):** `1m` (1 phút), `5m` (5 phút), `15m` (15 phút), `1h` (1 giờ), `4h` (4 giờ), `1d` (1 ngày), `1w` (1 tuần).
* **Cơ chế kỹ thuật cốt lõi (Critical Logic):**
    * Hệ thống **tuyệt đối không sử dụng cơ chế Polling** (gọi API tuần hoàn theo thời gian máy chủ) vì sẽ gây ra sai số và độ trễ do lệch clock.
    * Hệ thống phải lắng nghe luồng dữ liệu `Kline/Candlestick Streams` từ Binance WebSocket.
    * Trong cấu trúc payload trả về từ Binance, có trường dữ liệu mang nhãn `is_kline_closed` (hoặc ký hiệu `x` trong JSON raw).
    * **Logic xử lý tại Backend:**
        * Khi `x == false`: Cây nến hiện tại đang chạy. Backend có thể cập nhật giá trị tạm thời hoặc bỏ qua (tùy cấu hình tối ưu hiệu năng).
        * Khi `x == true`: Đây là thông điệp chính thức báo hiệu cây nến **đã đóng**. Backend phải lập tức bắt lấy gói tin này, đóng gói thành một Event có cấu trúc (gồm: Cặp tiền, Khung giờ, Open, High, Low, Close, Volume, Open Time, Close Time) và phát (Broadcast) đến tất cả Client đang kết nối.
* **Yêu cầu hiển thị trên UI:**
    * **Dạng bảng biểu (Data Table):** Dòng dữ liệu của khung giờ tương ứng phải cập nhật thông tin nến vừa đóng ở vị trí đầu tiên (hoặc hàng mới nhất), các thông số OHLCV chuyển từ trạng thái chuyển động sang trạng thái "đóng băng" (vì nến đã chốt).
    * **Dạng biểu đồ (Chart):** Vẽ thêm một thanh nến (candle bar) mới cứng trên biểu đồ kỹ thuật và chốt cố định hình dáng của cây nến cũ. Hành động này phải diễn ra mượt mà, không bị giật lag hay tải lại trang.

#### 3.3. Tính năng 3: Quản lý danh sách theo dõi (Watchlist Management)
* **Mô tả:** Người dùng có thể chọn các cặp giao dịch muốn theo dõi trên giao diện chính.
* **Yêu cầu hệ thống:**
    * Backend quản lý các kết nối WebSocket động dựa trên các cặp giao dịch đang được kích hoạt (Active) bởi người dùng trên hệ thống. Tránh việc kết nối thừa thãi tất cả các cặp trên Binance gây quá tải tài nguyên hệ thống.

---

### 4. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

#### 4.1. Hiệu năng và Độ trễ (Performance & Latency)
* **Độ trễ truyền tải:** Tổng thời gian tính từ khi Binance phát tín hiệu đóng nến (`x: true`) qua WebSocket -> Backend xử lý -> Đẩy qua WebSocket nội bộ -> Frontend nhận và hiển thị hoàn tất trên UI **phải nhỏ hơn 300ms** (Mục tiêu lý tưởng là < 150ms).
* **Giao thức kết nối Client-Server:** Bắt buộc sử dụng giao thức truyền tải hai chiều liên tục như **WebSocket** (hoặc WebTransport / Server-Sent Events). Nghiêm cấm dùng HTTP REST thông thường cho luồng dữ liệu này.

#### 4.2. Tính sẵn sàng và Khả năng chịu lỗi (Availability & Fault Tolerance)
* **Cơ chế Tự động kết nối lại (Auto-Reconnect):**
    * Binance giới hạn một kết nối WebSocket chỉ tồn tại tối đa 24 giờ. Hệ thống Backend phải triển khai cơ chế tự động làm mới kết nối (Connection Rotation / Reconnect) trước thời điểm bị ngắt 5 phút mà không làm gián đoạn luồng dữ liệu đẩy xuống client.
    * Khi xảy ra sự cố mất mạng internet hoặc mất kết nối đột ngột với Binance, hệ thống Backend phải tự động thử kết nối lại với chiến lược lũy thừa giảm dần (Exponential Backoff).
* **Cơ chế Bù đắp dữ liệu (Data Gap Filling):**
    * Trong trường hợp hệ thống mất kết nối với Binance trong vài giây/vài phút, một số sự kiện đóng nến có thể bị bỏ lỡ.
    * Ngay khi kết nối lại thành công, hệ thống phải tự động gọi **Binance REST API (`/api/v3/klines`)** để truy vấn lại dữ liệu của khoảng thời gian bị mất, so sánh và bù đắp (patch) vào cơ sở dữ liệu cũng như đồng bộ lại dữ liệu đúng cho UI của người dùng.

#### 4.3. Kiến trúc Đẩy dữ liệu (Scalability)
* Hệ thống phải chịu tải được tối thiểu **10,000 người dùng kết nối đồng thời (Concurrent Users)** xem dữ liệu real-time cùng một lúc mà không bị nghẽn băng thông hoặc tăng độ trễ tại Gateway.

---

### 5. ĐỀ XUẤT KIẾN TRÚC HỆ THỐNG SƠ BỘ (PROPOSED HIGH-LEVEL ARCHITECTURE)

Để đáp ứng các tiêu chuẩn khắt khe về thời gian thực và khả năng mở rộng, kiến trúc hệ thống được đề xuất chia tách thành các dịch vụ siêu nhỏ (Microservices) hoạt động theo mô hình hướng sự kiện (Event-Driven Architecture):

```
+------------------+                   +-----------------------+
|   Binance WS     |                   |   Binance REST API    |
+--------+---------+                   +-----------+-----------+
         | (Raw Stream)                            | (Fallback / Gap Fill)
         v                                         v
+--------------------------------------------------+-----------+
|               Data Fetcher Service (Worker)                  |
|  - Duy trì các kết nối WebSocket tới Binance                  |
|  - Lọc và bắt sự kiện `x: true` (Đóng nến)                   |
+------------------------+-------------------------------------+
                         |
                         v (Publish Event)
+--------------------------------------------------------------+
|             Message Queue / Pub-Sub (Redis/Kafka)            |
+------------------------+-------------------------------------+
                         |
                         v (Subscribe Event)
+--------------------------------------------------------------+
|                 API Gateway & WebSocket Server               |
|  - Quản lý hàng ngàn kết nối WebSocket từ phía trình duyệt    |
|  - Nhận sự kiện từ Pub-Sub và phát tán (Broadcast) xuống UI  |
+------------------------+-------------------------------------+
                         |
                         v (Real-time Push)
+--------------------------------------------------------------+
|                     User Interface (UI)                      |
|  - ReactJS / VueJS + TradingView Lightweight Charts         |
+--------------------------------------------------------------+
```

---

### 6. TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

* **AC 1 (Độ trễ nhảy giá):** Khi đặt màn hình ứng dụng cạnh màn hình trang chủ Binance.com, giá các cặp tiền tệ trên ứng dụng phải nhảy đồng bộ, độ lệch thời gian mắt thường nhìn thấy không được quá 0.5 giây.
* **AC 2 (Chốt nến chính xác):** Tại giây thứ `00` của một chu kỳ đóng nến (Ví dụ: 12:15:00 đối với nến 15m), hệ thống phải phát ra sự kiện đóng nến ngay lập tức. Dữ liệu giá đóng cửa (`Close Price`) hiển thị trên UI phải khớp 100% với giá đóng nến hiển thị trên đồ thị chính thức của Binance.
* **AC 3 (Kiểm tra đa khung giờ đồng thời):** Vào thời điểm kết thúc một giờ (Ví dụ: 13:00:00), hệ thống phải kích hoạt đồng thời sự kiện đóng nến của khung `1m`, `5m`, `15m` và `1h`. Giao diện của tất cả các khung này trên UI phải được cập nhật đồng loạt mà không bị lỗi đè dữ liệu hoặc bỏ sót khung giờ nào.
* **AC 4 (Khôi phục sau sự cố):** Thử nghiệm ngắt kết nối mạng của Worker trong vòng 30 giây rồi bật lại. Hệ thống phải tự động kết nối lại thành công, dữ liệu trên đồ thị UI không bị xuất hiện khoảng trắng (gap) mà phải được tự động điền đầy đủ dữ liệu của các nến đã đóng trong 30 giây mất mạng đó.
