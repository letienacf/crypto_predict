import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useWatchlistTicks } from "../hooks/useWatchlistTicks";
export function WatchlistPanel({ symbols, interval, activeSymbol, onSelectSymbol }) {
    const rows = useWatchlistTicks({ symbols, interval });
    return (_jsxs("section", { className: "panel panel--watchlist", children: [_jsxs("div", { className: "panel__header", children: [_jsx("h2", { children: "Watchlist" }), _jsx("span", { children: interval })] }), _jsx("div", { className: "watchlist-hint", children: "Click a symbol to load it into the main chart" }), _jsx("div", { className: "watchlist-grid", children: rows.map((row) => {
                    const rowSymbol = row.symbol;
                    const color = row.direction === "up" ? "#0ECB81" : row.direction === "down" ? "#F6465D" : "#E5E7EB";
                    const background = row.flashing
                        ? row.direction === "up"
                            ? "rgba(14, 203, 129, 0.18)"
                            : "rgba(246, 70, 93, 0.18)"
                        : "transparent";
                    const isActive = row.symbol === activeSymbol;
                    return (_jsxs("div", { className: isActive ? "watchlist-row watchlist-row--active" : "watchlist-row", style: row.flashing ? { backgroundColor: background } : undefined, role: "button", tabIndex: 0, onClick: () => onSelectSymbol(rowSymbol), onKeyDown: (event) => {
                            if (event.key === "Enter" || event.key === " ") {
                                event.preventDefault();
                                onSelectSymbol(rowSymbol);
                            }
                        }, children: [_jsx("strong", { style: { color: isActive ? "#F9FAFB" : "#9CA3AF" }, children: row.symbol.toUpperCase() }), _jsx("span", { style: { color, fontVariantNumeric: "tabular-nums" }, children: row.price === 0 ? "--" : row.price.toFixed(4) })] }, row.symbol));
                }) })] }));
}
