import { useEffect, useMemo, useRef, useState } from "react";

import { fetchHistoricalKlines } from "../api/marketApi";
import { MarketWsClient } from "../services/marketWsClient";
import type { Interval, KlineItem } from "../types/market";

interface UseHybridKlinesParams {
  symbol: string;
  interval: Interval;
  limit?: number;
}

export function useHybridKlines({ symbol, interval, limit = 1000 }: UseHybridKlinesParams): {
  klines: KlineItem[];
  isLoading: boolean;
  error: string | null;
} {
  const [klines, setKlines] = useState<KlineItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const wsClient = useMemo(() => new MarketWsClient(), []);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    let isDisposed = false;

    async function bootstrap(): Promise<void> {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetchHistoricalKlines(symbol, interval, limit);
        if (isDisposed) {
          return;
        }

        setKlines(response.data);

        wsClient.connect({ symbols: [symbol], intervals: [interval] });
        unsubscribeRef.current = wsClient.subscribe({
          symbol,
          interval,
          onKline: (incoming) => {
            setKlines((current) => {
              if (current.length === 0) {
                return [
                  {
                    timestamp: incoming.close_time,
                    open: incoming.open,
                    high: incoming.high,
                    low: incoming.low,
                    close: incoming.close,
                    volume: incoming.volume,
                  },
                ];
              }

              const next = [...current];
              const last = next[next.length - 1];

              if (last.timestamp === incoming.close_time) {
                next[next.length - 1] = {
                  timestamp: incoming.close_time,
                  open: incoming.open,
                  high: incoming.high,
                  low: incoming.low,
                  close: incoming.close,
                  volume: incoming.volume,
                };
                return next;
              }

              next.push({
                timestamp: incoming.close_time,
                open: incoming.open,
                high: incoming.high,
                low: incoming.low,
                close: incoming.close,
                volume: incoming.volume,
              });

              return next.slice(-limit);
            });
          },
        });
      } catch (caught: unknown) {
        const message = caught instanceof Error ? caught.message : "Unknown error";
        if (!isDisposed) {
          setError(message);
        }
      } finally {
        if (!isDisposed) {
          setIsLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      isDisposed = true;
      if (unsubscribeRef.current !== null) {
        unsubscribeRef.current();
      }
      wsClient.close();
    };
  }, [symbol, interval, limit, wsClient]);

  return { klines, isLoading, error };
}
