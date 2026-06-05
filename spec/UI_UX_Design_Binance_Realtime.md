# THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (UI/UX DESIGN) VÀ KIẾN TRÚC FRONTEND
## DỰ ÁN: BINANCE REAL-TIME MARKET DATA TRACKER

---

### 1. PHONG CÁCH THIẾT KẾ (DESIGN SYSTEM)
Giao diện Trading đòi hỏi sự tập trung cực độ, do đó phong cách thiết kế sẽ mang hơi hướng **hiện đại, tối màu (Dark Mode First)**, tối giản chi tiết thừa và nhấn mạnh vào chuyển động của con số.

* **Bảng màu (Color Palette):**
    * **Background (Nền):** Tối sâu để làm nổi bật biểu đồ - `#0B0E11` hoặc `#161A1E` (Tương đồng chuẩn Binance/TradingView).
    * **Surface (Khối nổi):** `#1E2329` (Cho các panel, khu vực sidebar, dropdown, modal).
    * **Primary (Màu chủ đạo):** `#FCD535` (Vàng Binance) dùng cho CTA, nút bấm chính hoặc viền focus.
    * **Semantic Colors (Màu trạng thái cực kỳ quan trọng):**
        * Tăng giá (Bullish): `#0ECB81` (Xanh lá).
        * Giảm giá (Bearish): `#F6465D` (Đỏ).
* **Typography:**
    * **Font chữ tổng thể:** `Inter` hoặc `Roboto` - Đây là các font không chân (Sans-serif) có độ đọc cực tốt cho giao diện dashboard.
    * **Font số (Monospace):** Bắt buộc dùng font Monospace (ví dụ: `Roboto Mono`, `JetBrains Mono` hoặc `Fira Code`) cho khu vực giá nhảy. Việc này đảm bảo các con số căn gióng thẳng hàng dọc, không bị thụt ra thụt vào khi một con số (như số "1") thay đổi thành số khác (như số "8").
* **Hiệu ứng (Animations):**
    * **Flash Effect (Hiệu ứng chớp):** Khi giá thay đổi, background của ô chứa giá (hoặc chữ số đó) lóe lên màu xanh/đỏ mờ (opacity 20%) trong 150ms rồi tắt dần đi. Tuyệt đối không dùng hiệu ứng kéo dài làm mỏi mắt.

---

### 2. BỐ CỤC MÀN HÌNH CHÍNH (MAIN WORKSPACE LAYOUT)
Hệ thống sử dụng bố cục linh hoạt dạng **Grid/Panel (Docking System)** giúp Trader tập trung theo dõi đa khung thời gian nhưng không bị phân tán.

#### 2.1. Thanh điều hướng trên cùng (Top Navigation Bar)
* **Logo & Tên App:** Góc trái.
* **Bộ chọn Cặp tiền (Symbol Selector):** Dropdown tìm kiếm nhanh (VD: gõ "BTC", ra list BTCUSDT, BTCEUR...). Đi kèm với con số giá hiện tại và % thay đổi trong 24h thu nhỏ ngay trên thanh nav.
* **Settings & User Profile:** Nút chỉnh sửa giao diện (Chế độ Sáng/Tối), cài đặt ngôn ngữ ở góc phải.

#### 2.2. Khu vực trung tâm: Bảng vẽ biểu đồ (The Chart Area)
Đây là trái tim của ứng dụng, chiếm 75% không gian hiển thị, chia làm hai dải công cụ:

* **Thanh công cụ trên biểu đồ (Chart Toolbar):**
    * **Khung thời gian (Timeframes):** Các nút bấm nối tiếp: `1m` | `5m` | `15m` | `1H` | `4H` | `1D` | `1W`. Nút nào đang Active sẽ sáng màu.
    * **Loại biểu đồ:** Dropdown chọn Nến Nhật (Candles - mặc định), Đường thẳng (Line), Thanh (Bars).
    * **Nút "Indicators" (Fx):** Nút gọi Modal danh sách các chỉ báo kỹ thuật (RSI, MACD, Bollinger Bands...).
* **Canvas Biểu đồ chính:**
    * Sử dụng thư viện `TradingView Lightweight Charts`.
    * Biểu đồ hiển thị nến. Bên phải là trục giá (Y-axis), bên dưới là trục thời gian (X-axis).
    * **Sub-panes (Ngăn phụ):** Nếu bật Indicator dao động (ví dụ Volume, RSI, MACD), một ngăn phụ sẽ tự động gắn kết nối tiếp xuống bên dưới đồ thị giá chính.

#### 2.3. Bảng bên phải: Watchlist & Dữ liệu Tick (Right Sidebar)
Chiếm 25% màn hình còn lại.
* **Tab 1: Watchlist:**
    * Liệt kê các cặp coin người dùng quan tâm. Mỗi hàng gồm: Tên cặp (bên trái), Giá hiện tại và % biến động (bên phải - liên tục nhấp nháy xanh đỏ).
    * Có thể kéo thả (Drag & Drop) để tự sắp xếp thứ tự ưu tiên.
* **Tab 2: Nến hiện tại (Live Candle Stats):**
    * Tách riêng khu vực hiển thị các thông số O (Open), H (High), L (Low), C (Close), V (Volume) của cây nến đang chạy thuộc khung giờ đang chọn trên Chart.
    * **Bộ đếm lùi (Countdown Timer):** Chữ đếm ngược to và rõ (VD: `00:04:12`) báo hiệu thời gian còn lại trước khi cây nến hiện tại chính thức chốt giá (is_closed: true).

---

### 3. LUỒNG TƯƠNG TÁC CHO TÍNH NĂNG INDICATORS (UX CHO MỞ RỘNG TƯƠNG LAI)
Tính năng Indicator cần một luồng thao tác UX rõ ràng để Trader tự do tùy chỉnh thông số theo công thức riêng của họ.

1. **Thêm Indicator:**
   * User bấm nút `[Fx Indicators]` trên Chart Toolbar.
   * Một Modal bật lên (dạng Searchable List) gồm các Indicator đã được Backend hoặc Client hỗ trợ tính toán.
   * User bấm chọn `RSI`.
2. **Cài đặt thông số (Setting Indicator):**
   * Trong góc trên cùng bên trái của Sub-pane RSI vừa xuất hiện dưới biểu đồ, có hiển thị tên "RSI(14)" kèm theo icon hình bánh răng ⚙️ (Settings).
   * Bấm vào bánh răng, Modal setting hiện ra với các tab:
      * *Inputs (Tham số đầu vào):* Ô input số cho chu kỳ (Length - Mặc định 14). Nguồn dữ liệu (Source - Close/Open).
      * *Style (Kiểu dáng):* Bảng màu chọn màu đường tín hiệu RSI, chọn độ dày viền, tùy chỉnh giá trị và màu sắc của vùng Overbought (70), Oversold (30).
   * Khi User bấm "Apply", nếu Indicator tính toán ở Client, chart tự vẽ lại ngay. Nếu tính ở Server (Backend tính bằng TA-Lib), Frontend sẽ phát lệnh cấu hình qua API.
3. **Hiển thị Real-time:** Giá trị chót của RSI (VD: `RSI: 45.12`) tại nến hiện tại sẽ nhảy số liên tục theo mỗi cú Tick giá, đồng bộ theo thời gian thực tuyệt đối với chuyển động của biểu đồ nến phía trên.

---

### 4. THIẾT KẾ CẤU TRÚC FRONTEND (REACT.JS ARCHITECTURE)

Để đáp ứng thiết kế trên và ngăn chặn tình trạng phình to bộ nhớ (Memory Leak) hoặc giật lag do React "re-render" lại toàn bộ trang nhiều lần mỗi giây khi giá nhảy, kiến trúc nên được tổ chức như sau:

#### 4.1. Phân tầng Component (Component Tree)
```html
<App>
  <TopNavbar /> <!-- Chỉ render lại khi đổi User, đổi Pair -->
  
  <Workspace>
     <MainChartArea>
         <ChartToolbar />     <!-- Quản lý state Timeframe cục bộ, mở Modal Indicator -->
         <TradingViewChart /> <!-- THÀNH PHẦN LÕI: Ref gắn thẳng vào DOM, không dùng state react cho data -->
     </MainChartArea>
     
     <RightSidebar>
         <Watchlist />        <!-- Thành phần này tự kết nối một luồng Context/Zustand tối ưu để update giá độc lập -->
         <LiveCandleStats />  <!-- Subscribe vào luồng kline_update -->
     </RightSidebar>
  </Workspace>
  
  <IndicatorSettingModal />
</App>
```

#### 4.2. Chiến lược xử lý DOM (Performance Optimization)
**Nguyên tắc vàng:** KHÔNG đưa dữ liệu streaming tốc độ cao (như Tick giá 100ms/lần) vào luồng `setState` chuẩn của React đối với các component khổng lồ.

```javascript
// ❌ CÁCH LÀM SAI (Sẽ gây giật lag nghiêm trọng vì ép React tính toán Virtual DOM liên tục):
const [candles, setCandles] = useState([]);
ws.onmessage = (msg) => setCandles(prev => [...prev, JSON.parse(msg.data)]);
// <Chart data={candles} />

// ✅ CÁCH LÀM ĐÚNG BÀI BẢN (Thao tác trực tiếp vào thư viện Lightweight Charts):
import { createChart } from 'lightweight-charts';

const TradingViewChart = ({ currentSymbol, currentInterval }) => {
    const chartContainerRef = useRef(null);
    const candleSeriesRef = useRef(null);

    useEffect(() => {
        // 1. Dựng khung biểu đồ ban đầu
        const chart = createChart(chartContainerRef.current, { 
            layout: { background: { type: 'solid', color: '#161A1E' }, textColor: '#D9D9D9' },
            grid: { vertLines: { color: '#2B3139' }, horzLines: { color: '#2B3139' } }
        });
        candleSeriesRef.current = chart.addCandlestickSeries({
            upColor: '#0ECB81', downColor: '#F6465D', borderVisible: false, wickUpColor: '#0ECB81', wickDownColor: '#F6465D'
        });
        
        // 2. Fetch quá khứ (Chiến lược Hybrid Load: Lấy 1000 nến REST API)
        fetchHistoricalData(currentSymbol, currentInterval).then(historicalData => {
            candleSeriesRef.current.setData(historicalData); // Hàm nội tại của thư viện
        });
        
        // 3. Nối ống WebSocket và cập nhật "Trực tiếp" qua con trỏ nhớ (ref)
        const ws = new WebSocket('wss://your-backend.com/ws/market');
        ws.onmessage = (event) => {
            const liveCandle = JSON.parse(event.data);
            // Bơm thẳng dữ liệu vào thư viện gốc, BỎ QUA hoàn toàn vòng đời re-render của React
            if (candleSeriesRef.current) {
                candleSeriesRef.current.update(liveCandle);
            }
        };

        // 4. Clean up khi Component bị tháo gỡ (Unmount)
        return () => {
            ws.close();
            chart.remove();
        };
    }, [currentSymbol, currentInterval]); // Chỉ render lại từ đầu nếu người dùng đổi Cặp tiền hoặc Khung giờ

    return <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />;
};
```
