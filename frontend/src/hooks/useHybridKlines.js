import { useEffect, useMemo, useRef, useState } from "react";
import { fetchHistoricalKlines } from "../api/marketApi";
import { MarketWsClient } from "../services/marketWsClient";
function normalizeCandles(candles, limit) {
    const byTimestamp = new Map();
    for (const candle of candles) {
        const canonicalTimestamp = new Date(Math.floor(new Date(candle.timestamp).getTime() / 1000) * 1000).toISOString();
        byTimestamp.set(canonicalTimestamp, {
            ...candle,
            timestamp: canonicalTimestamp,
        });
    }
    return [...byTimestamp.values()]
        .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
        .slice(-limit);
}
function upsertCandle(current, incoming, limit) {
    const canonicalTimestamp = new Date(Math.floor(new Date(incoming.timestamp).getTime() / 1000) * 1000).toISOString();
    const normalizedIncoming = {
        ...incoming,
        timestamp: canonicalTimestamp,
    };
    const index = current.findIndex((item) => item.timestamp === canonicalTimestamp);
    if (index >= 0) {
        const next = [...current];
        next[index] = normalizedIncoming;
        return normalizeCandles(next, limit);
    }
    return normalizeCandles([...current, normalizedIncoming], limit);
}
function intervalToMs(interval) {
    switch (interval) {
        case "1m":
            return 60_000;
        case "5m":
            return 5 * 60_000;
        case "15m":
            return 15 * 60_000;
        case "1h":
            return 60 * 60_000;
        case "4h":
            return 4 * 60 * 60_000;
        case "1d":
            return 24 * 60 * 60_000;
        case "1w":
            return 7 * 24 * 60 * 60_000;
        default:
            return 60_000;
    }
}
function getCandleCloseTimeMs(timeMs, intervalMs) {
    // Binance kline close_time is end-of-window (e.g. 12:00:59.999 for 1m),
    // so we keep the same semantic on the client to avoid duplicate live candles.
    return Math.floor(timeMs / intervalMs) * intervalMs + intervalMs - 1000;
}
function advanceLiveCandle(current, nowMs, intervalMs, limit) {
    if (current.length === 0) {
        return current;
    }
    const next = [...current];
    const last = next[next.length - 1];
    const lastCloseMs = new Date(last.timestamp).getTime();
    if (Number.isNaN(lastCloseMs)) {
        return current;
    }
    const desiredCloseMs = getCandleCloseTimeMs(nowMs, intervalMs);
    if (lastCloseMs >= desiredCloseMs) {
        return current;
    }
    let cursorCloseMs = lastCloseMs;
    const baseClose = last.close;
    let iterations = 0;
    while (cursorCloseMs < desiredCloseMs && iterations < 12) {
        cursorCloseMs += intervalMs;
        next.push({
            timestamp: new Date(Math.floor(cursorCloseMs / 1000) * 1000).toISOString(),
            open: baseClose,
            high: baseClose,
            low: baseClose,
            close: baseClose,
            volume: 0,
        });
        iterations += 1;
    }
    return normalizeCandles(next, limit);
}
export function useHybridKlines({ symbol, interval, limit = 1000, nowMs }) {
    const [klines, setKlines] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const wsClient = useMemo(() => new MarketWsClient(), []);
    const unsubscribeKlineRef = useRef(null);
    const unsubscribeTickRef = useRef(null);
    useEffect(() => {
        let isDisposed = false;
        const intervalMs = intervalToMs(interval);
        async function bootstrap() {
            setIsLoading(true);
            setError(null);
            try {
                const response = await fetchHistoricalKlines(symbol, interval, limit);
                if (isDisposed) {
                    return;
                }
                setKlines(normalizeCandles(response.data, limit));
                wsClient.connect({ symbols: [symbol], intervals: [interval] });
                unsubscribeKlineRef.current = wsClient.subscribe({
                    symbol,
                    interval,
                    onKline: (incoming) => {
                        setKlines((current) => {
                            const normalizedIncoming = {
                                timestamp: incoming.close_time,
                                open: incoming.open,
                                high: incoming.high,
                                low: incoming.low,
                                close: incoming.close,
                                volume: incoming.volume,
                            };
                            return upsertCandle(current, normalizedIncoming, limit);
                        });
                    },
                });
                unsubscribeTickRef.current = wsClient.subscribeTick({
                    symbol,
                    onTick: (tick) => {
                        setKlines((current) => {
                            if (current.length === 0) {
                                return current;
                            }
                            const tradeTimeMs = new Date(tick.trade_time).getTime();
                            if (Number.isNaN(tradeTimeMs)) {
                                return current;
                            }
                            const next = [...current];
                            const last = next[next.length - 1];
                            const lastCloseMs = new Date(last.timestamp).getTime();
                            if (Number.isNaN(lastCloseMs)) {
                                return current;
                            }
                            const currentCloseMs = getCandleCloseTimeMs(tradeTimeMs, intervalMs);
                            if (currentCloseMs <= lastCloseMs) {
                                const updatedLast = {
                                    ...last,
                                    high: Math.max(last.high, tick.price),
                                    low: Math.min(last.low, tick.price),
                                    close: tick.price,
                                    volume: last.volume + tick.quantity,
                                };
                                return upsertCandle(next.slice(0, -1), updatedLast, limit);
                            }
                            const newCandle = {
                                timestamp: new Date(Math.floor(currentCloseMs / 1000) * 1000).toISOString(),
                                open: last.close,
                                high: Math.max(last.close, tick.price),
                                low: Math.min(last.close, tick.price),
                                close: tick.price,
                                volume: tick.quantity,
                            };
                            return upsertCandle(next, newCandle, limit);
                        });
                    },
                });
            }
            catch (caught) {
                const message = caught instanceof Error ? caught.message : "Unknown error";
                if (!isDisposed) {
                    setError(message);
                }
            }
            finally {
                if (!isDisposed) {
                    setIsLoading(false);
                }
            }
        }
        bootstrap();
        return () => {
            isDisposed = true;
            if (unsubscribeKlineRef.current !== null) {
                unsubscribeKlineRef.current();
            }
            if (unsubscribeTickRef.current !== null) {
                unsubscribeTickRef.current();
            }
            wsClient.close();
        };
    }, [symbol, interval, limit, wsClient]);
    useEffect(() => {
        if (nowMs === undefined) {
            return;
        }
        const intervalMs = intervalToMs(interval);
        setKlines((current) => advanceLiveCandle(current, nowMs, intervalMs, limit));
    }, [interval, limit, nowMs]);
    return { klines, isLoading, error };
}
