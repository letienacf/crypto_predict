import { useEffect, useMemo, useRef, useState } from "react";
import { fetchHistoricalKlines } from "../api/marketApi";
import { MarketWsClient } from "../services/marketWsClient";
export function useWatchlistTicks({ symbols, interval }) {
    const [rows, setRows] = useState(symbols.map((symbol) => ({ symbol: symbol.toLowerCase(), price: 0, direction: "none", flashing: false })));
    const wsClient = useMemo(() => new MarketWsClient(), []);
    const unsubscribesRef = useRef([]);
    const timersRef = useRef(new Map());
    useEffect(() => {
        let disposed = false;
        setRows(symbols.map((symbol) => ({ symbol: symbol.toLowerCase(), price: 0, direction: "none", flashing: false })));
        const hydrateFromRest = async () => {
            const snapshots = await Promise.all(symbols.map(async (symbol) => {
                try {
                    const response = await fetchHistoricalKlines(symbol, interval, 1);
                    const last = response.data[response.data.length - 1];
                    return { symbol: symbol.toLowerCase(), price: last?.close ?? 0 };
                }
                catch {
                    return { symbol: symbol.toLowerCase(), price: 0 };
                }
            }));
            if (disposed) {
                return;
            }
            setRows((current) => current.map((row) => {
                const snapshot = snapshots.find((item) => item.symbol === row.symbol);
                if (snapshot === undefined || snapshot.price <= 0) {
                    return row;
                }
                const direction = row.price === 0 ? "none" : snapshot.price > row.price ? "up" : snapshot.price < row.price ? "down" : "none";
                return {
                    ...row,
                    price: snapshot.price,
                    direction,
                };
            }));
        };
        void hydrateFromRest();
        const pollingTimer = window.setInterval(() => {
            void hydrateFromRest();
        }, 10000);
        wsClient.connect({ symbols, intervals: [interval] });
        wsClient.updateWatchlist(symbols, [interval]);
        unsubscribesRef.current = symbols.map((symbol) => {
            const normalized = symbol.toLowerCase();
            return wsClient.subscribeTick({
                symbol: normalized,
                onTick: (tick) => {
                    setRows((current) => current.map((row) => {
                        if (row.symbol !== tick.symbol) {
                            return row;
                        }
                        const direction = row.price === 0 ? "none" : tick.price > row.price ? "up" : tick.price < row.price ? "down" : "none";
                        const existingTimer = timersRef.current.get(row.symbol);
                        if (existingTimer !== undefined) {
                            window.clearTimeout(existingTimer);
                        }
                        const timerId = window.setTimeout(() => {
                            setRows((nextRows) => nextRows.map((nextRow) => nextRow.symbol === row.symbol ? { ...nextRow, flashing: false } : nextRow));
                        }, 150);
                        timersRef.current.set(row.symbol, timerId);
                        return {
                            ...row,
                            price: tick.price,
                            direction,
                            flashing: direction !== "none",
                        };
                    }));
                },
            });
        });
        return () => {
            disposed = true;
            window.clearInterval(pollingTimer);
            for (const unsubscribe of unsubscribesRef.current) {
                unsubscribe();
            }
            unsubscribesRef.current = [];
            for (const timer of timersRef.current.values()) {
                window.clearTimeout(timer);
            }
            timersRef.current.clear();
            wsClient.close();
        };
    }, [symbols, interval, wsClient]);
    return rows;
}
