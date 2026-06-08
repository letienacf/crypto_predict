import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
function formatCountdown(totalSeconds) {
    const seconds = Math.max(totalSeconds, 0);
    const minutes = Math.floor(seconds / 60);
    const remainSeconds = seconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}
export function LiveCandleStats({ symbol, interval, latestCandle, nowMs, offsetMs }) {
    const closeMs = latestCandle === null ? 0 : new Date(latestCandle.timestamp).getTime();
    const countdownSec = closeMs > 0 ? Math.floor((closeMs - nowMs) / 1000) : 0;
    return (_jsxs("section", { className: "panel panel--stats", children: [_jsxs("div", { className: "panel__header", children: [_jsx("h2", { children: "Live Candle Stats" }), _jsx("span", { children: "Server sync" })] }), _jsxs("p", { className: "panel__meta", children: [symbol.toUpperCase(), " ", interval, " | Server offset: ", offsetMs, " ms"] }), latestCandle === null ? (_jsx("p", { className: "panel__empty", children: "No active candle yet." })) : (_jsxs("div", { className: "stats-grid", children: [_jsxs("div", { className: "stats-item", children: [_jsx("span", { children: "Open" }), _jsx("strong", { children: latestCandle.open.toFixed(4) })] }), _jsxs("div", { className: "stats-item", children: [_jsx("span", { children: "High" }), _jsx("strong", { children: latestCandle.high.toFixed(4) })] }), _jsxs("div", { className: "stats-item", children: [_jsx("span", { children: "Low" }), _jsx("strong", { children: latestCandle.low.toFixed(4) })] }), _jsxs("div", { className: "stats-item", children: [_jsx("span", { children: "Close" }), _jsx("strong", { children: latestCandle.close.toFixed(4) })] }), _jsxs("div", { className: "stats-item stats-item--full", children: [_jsx("span", { children: "Volume" }), _jsx("strong", { children: latestCandle.volume.toFixed(4) })] }), _jsxs("div", { className: "stats-item stats-item--full stats-item--countdown", children: [_jsx("span", { children: "Countdown" }), _jsx("strong", { children: formatCountdown(countdownSec) })] })] }))] }));
}
