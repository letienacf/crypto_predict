import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { LiveCandleStats } from "./components/LiveCandleStats";
import { OrderBookPanel } from "./components/OrderBookPanel";
import { RealtimeCandlestickChart } from "./components/RealtimeCandlestickChart";
import { WatchlistPanel } from "./components/WatchlistPanel";
import { useHybridKlines } from "./hooks/useHybridKlines";
import { useServerTime } from "./hooks/useServerTime";
const AVAILABLE_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt", "solusdt"];
const AVAILABLE_INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"];
const USER_PREFERENCES_STORAGE_KEY = "crypto_predict.user_preferences.v1";
function isMarketSymbol(value) {
    return AVAILABLE_SYMBOLS.includes(value);
}
function isInterval(value) {
    return AVAILABLE_INTERVALS.includes(value);
}
function loadUserPreferences() {
    const fallback = { symbol: "btcusdt", interval: "5m" };
    if (typeof window === "undefined") {
        return fallback;
    }
    try {
        const raw = window.localStorage.getItem(USER_PREFERENCES_STORAGE_KEY);
        if (raw === null) {
            return fallback;
        }
        const parsed = JSON.parse(raw);
        const nextSymbol = typeof parsed.symbol === "string" && isMarketSymbol(parsed.symbol) ? parsed.symbol : fallback.symbol;
        const nextInterval = typeof parsed.interval === "string" && isInterval(parsed.interval) ? parsed.interval : fallback.interval;
        return { symbol: nextSymbol, interval: nextInterval };
    }
    catch {
        return fallback;
    }
}
export function App() {
    const [initialPreferences] = useState(loadUserPreferences);
    const [symbol, setSymbol] = useState(initialPreferences.symbol);
    const [interval, setInterval] = useState(initialPreferences.interval);
    const { nowMs, offsetMs } = useServerTime();
    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        const preferences = { symbol, interval };
        window.localStorage.setItem(USER_PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
    }, [symbol, interval]);
    const { klines, isLoading, error } = useHybridKlines({ symbol, interval, limit: 1000, nowMs });
    const latestCandle = klines.length > 0 ? klines[klines.length - 1] : null;
    const previousCandle = klines.length > 1 ? klines[klines.length - 2] : null;
    const changePercent = useMemo(() => {
        if (latestCandle === null || previousCandle === null || previousCandle.close === 0) {
            return 0;
        }
        return ((latestCandle.close - previousCandle.close) / previousCandle.close) * 100;
    }, [latestCandle, previousCandle]);
    const priceDirection = changePercent > 0 ? "up" : changePercent < 0 ? "down" : "flat";
    const lastPriceText = latestCandle === null ? "--" : latestCandle.close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (_jsxs("main", { className: "app-shell", children: [_jsxs("header", { className: "terminal-header", children: [_jsxs("div", { className: "terminal-header__left", children: [_jsx("div", { className: "brand", children: "CRYPTO PREDICT PRO" }), _jsxs("div", { className: "market-title", children: [_jsx("strong", { children: symbol.toUpperCase().replace("USDT", "/USDT") }), _jsx("span", { children: interval })] }), _jsxs("div", { className: "market-price", children: [_jsx("strong", { className: priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : "", children: lastPriceText }), _jsxs("span", { className: priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : "", children: [priceDirection === "up" ? "+" : "", changePercent.toFixed(2), "%"] })] })] }), _jsx("div", { className: "terminal-header__right", children: _jsx("span", { className: error !== null ? "status status--error" : isLoading ? "status" : "status status--live", children: error !== null ? "Issue" : isLoading ? "Syncing" : "Live" }) })] }), _jsxs("section", { className: "terminal-workspace", children: [_jsxs("aside", { className: "left-tools", children: [_jsx("button", { type: "button", title: "Crosshair", children: "\u2316" }), _jsx("button", { type: "button", title: "Trendline", children: "\uFF0F" }), _jsx("button", { type: "button", title: "Fib", children: "\u0192x" }), _jsx("button", { type: "button", title: "Brush", children: "\u270E" }), _jsx("button", { type: "button", title: "Settings", children: "\u2699" })] }), _jsxs("section", { className: "chart-zone", children: [_jsxs("div", { className: "chart-toolbar", children: [_jsx("div", { className: "pill-row", role: "tablist", "aria-label": "Timeframe selector", children: AVAILABLE_INTERVALS.map((item) => (_jsx("button", { type: "button", className: item === interval ? "pill pill--active" : "pill", onClick: () => setInterval(item), children: item }, item))) }), _jsxs("div", { className: "chart-toolbar__actions", children: [_jsx("button", { type: "button", className: "ghost-button", children: "Indicators" }), _jsx("button", { type: "button", className: "ghost-button", children: "Compare" }), _jsx("button", { type: "button", className: "ghost-button", children: "Alert" })] })] }), _jsxs("div", { className: "chart-stage panel", children: [_jsxs("div", { className: "chart-stage__stats mono", children: [_jsxs("span", { children: ["O ", latestCandle?.open.toFixed(2) ?? "--"] }), _jsxs("span", { children: ["H ", latestCandle?.high.toFixed(2) ?? "--"] }), _jsxs("span", { children: ["L ", latestCandle?.low.toFixed(2) ?? "--"] }), _jsxs("span", { className: priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : "", children: ["C ", latestCandle?.close.toFixed(2) ?? "--"] })] }), _jsx(RealtimeCandlestickChart, { klines: klines })] }), _jsx(OrderBookPanel, { lastPrice: latestCandle?.close ?? 10000 })] }), _jsxs("aside", { className: "right-sidebar", children: [_jsx(WatchlistPanel, { symbols: AVAILABLE_SYMBOLS, interval: interval, activeSymbol: symbol, onSelectSymbol: setSymbol }), _jsx(LiveCandleStats, { symbol: symbol, interval: interval, latestCandle: latestCandle, nowMs: nowMs, offsetMs: offsetMs })] })] })] }));
}
