import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo } from "react";
function formatPrice(value) {
    return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function formatAmount(value) {
    return value.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}
function buildRows(lastPrice, isAsk) {
    const rows = [];
    for (let i = 1; i <= 8; i += 1) {
        const step = 2 + i * 0.8;
        const price = isAsk ? lastPrice + step : lastPrice - step;
        const amount = 0.2 + i * 0.08;
        rows.push({
            price,
            amount,
            total: price * amount,
            depth: 14 + i * 6,
        });
    }
    return rows;
}
export function OrderBookPanel({ lastPrice }) {
    const asks = useMemo(() => buildRows(lastPrice, true).reverse(), [lastPrice]);
    const bids = useMemo(() => buildRows(lastPrice, false), [lastPrice]);
    return (_jsxs("section", { className: "panel panel--orderbook panel--orderbook-bottom", children: [_jsxs("div", { className: "panel__header", children: [_jsx("h2", { children: "Order Book" }), _jsx("span", { children: "Depth 24" })] }), _jsxs("div", { className: "orderbook-head orderbook-head--split", children: [_jsx("span", { className: "text-up", children: "Bids" }), _jsxs("span", { className: "orderbook-head__price", children: ["Last ", formatPrice(lastPrice)] }), _jsx("span", { className: "text-down", children: "Asks" })] }), _jsxs("div", { className: "orderbook-grid", children: [_jsx("div", { className: "orderbook-column orderbook-column--bid", children: bids.map((row) => (_jsxs("div", { className: "orderbook-row orderbook-row--bid", children: [_jsx("div", { className: "orderbook-row__depth", style: { width: `${row.depth}%` } }), _jsx("span", { className: "mono text-up", children: formatPrice(row.price) }), _jsx("span", { className: "mono", children: formatAmount(row.amount) }), _jsx("span", { className: "mono", children: formatPrice(row.total) })] }, `bid-${row.price}`))) }), _jsx("div", { className: "orderbook-column orderbook-column--ask", children: asks.map((row) => (_jsxs("div", { className: "orderbook-row orderbook-row--ask", children: [_jsx("div", { className: "orderbook-row__depth", style: { width: `${row.depth}%` } }), _jsx("span", { className: "mono text-down", children: formatPrice(row.price) }), _jsx("span", { className: "mono", children: formatAmount(row.amount) }), _jsx("span", { className: "mono", children: formatPrice(row.total) })] }, `ask-${row.price}`))) })] })] }));
}
