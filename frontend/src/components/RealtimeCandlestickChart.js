import { jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useRef } from "react";
import { ColorType, CandlestickSeries, createChart, } from "lightweight-charts";
const VN_TIMEZONE = "Asia/Ho_Chi_Minh";
const VN_TIME_FORMATTER = new Intl.DateTimeFormat("vi-VN", {
    timeZone: VN_TIMEZONE,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
});
const VN_DATE_TIME_FORMATTER = new Intl.DateTimeFormat("vi-VN", {
    timeZone: VN_TIMEZONE,
    year: "2-digit",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
});
function toUnixSeconds(time) {
    if (typeof time === "number") {
        return time;
    }
    if (typeof time === "string") {
        return Math.floor(new Date(`${time}T00:00:00Z`).getTime() / 1000);
    }
    return Math.floor(Date.UTC(time.year, time.month - 1, time.day) / 1000);
}
function toCandle(kline) {
    return {
        time: Math.floor(new Date(kline.timestamp).getTime() / 1000),
        open: kline.open,
        high: kline.high,
        low: kline.low,
        close: kline.close,
    };
}
function normalizeForChart(klines) {
    const byTime = new Map();
    for (const kline of klines) {
        const candle = toCandle(kline);
        byTime.set(Number(candle.time), candle);
    }
    return [...byTime.values()].sort((a, b) => Number(a.time) - Number(b.time));
}
export function RealtimeCandlestickChart({ klines }) {
    const containerRef = useRef(null);
    const chartRef = useRef(null);
    const seriesRef = useRef(null);
    useEffect(() => {
        if (containerRef.current === null || chartRef.current !== null) {
            return;
        }
        const chart = createChart(containerRef.current, {
            localization: {
                locale: "vi-VN",
                timeFormatter: (time) => VN_DATE_TIME_FORMATTER.format(new Date(toUnixSeconds(time) * 1000)),
            },
            layout: {
                background: { type: ColorType.Solid, color: "#0b0e11" },
                textColor: "#848e9c",
            },
            grid: {
                vertLines: { color: "#1e2329" },
                horzLines: { color: "#1e2329" },
            },
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight,
            autoSize: true,
            crosshair: {
                vertLine: {
                    color: "#474d57",
                    width: 1,
                    style: 1,
                    labelBackgroundColor: "#474d57",
                },
                horzLine: {
                    color: "#474d57",
                    width: 1,
                    style: 1,
                    labelBackgroundColor: "#474d57",
                },
                mode: 1,
            },
            rightPriceScale: {
                borderColor: "#2b3139",
                scaleMargins: {
                    top: 0.08,
                    bottom: 0.1,
                },
            },
            timeScale: {
                borderColor: "#2b3139",
                timeVisible: true,
                secondsVisible: false,
                tickMarkFormatter: (time) => VN_TIME_FORMATTER.format(new Date(toUnixSeconds(time) * 1000)),
                rightOffset: 50,
                shiftVisibleRangeOnNewBar: true,
            },
            handleScale: {
                mouseWheel: true,
                axisPressedMouseMove: true,
                pinch: true,
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            },
        });
        const series = chart.addSeries(CandlestickSeries, {
            upColor: "#0ecb81",
            downColor: "#f6465d",
            borderVisible: false,
            wickUpColor: "#0ecb81",
            wickDownColor: "#f6465d",
        });
        chartRef.current = chart;
        seriesRef.current = series;
        const resizeObserver = new ResizeObserver(() => {
            if (containerRef.current !== null && chartRef.current !== null) {
                chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
            }
        });
        resizeObserver.observe(containerRef.current);
        return () => {
            resizeObserver.disconnect();
            chart.remove();
            chartRef.current = null;
            seriesRef.current = null;
        };
    }, []);
    useEffect(() => {
        const series = seriesRef.current;
        const chart = chartRef.current;
        if (series === null || chart === null || klines.length === 0) {
            return;
        }
        const candles = normalizeForChart(klines);
        series.setData(candles);
        chart.timeScale().scrollToRealTime();
    }, [klines]);
    return _jsx("div", { ref: containerRef, className: "chart-canvas" });
}
