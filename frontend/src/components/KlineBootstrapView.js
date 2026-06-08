import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useHybridKlines } from "../hooks/useHybridKlines";
export function KlineBootstrapView({ symbol, interval }) {
    const { klines, isLoading, error } = useHybridKlines({ symbol, interval, limit: 200 });
    if (isLoading) {
        return _jsx("p", { children: "Loading historical candles..." });
    }
    if (error !== null) {
        return _jsxs("p", { children: ["Error: ", error] });
    }
    const last = klines[klines.length - 1];
    return (_jsxs("section", { children: [_jsxs("h2", { children: ["Hybrid stream active for ", symbol.toUpperCase(), " ", interval] }), _jsxs("p", { children: ["Total candles in memory: ", klines.length] }), last !== undefined ? (_jsxs("p", { children: ["Last close: ", last.close, " | High: ", last.high, " | Low: ", last.low] })) : (_jsx("p", { children: "No data yet." }))] }));
}
