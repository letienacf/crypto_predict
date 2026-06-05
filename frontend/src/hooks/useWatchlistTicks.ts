import { useEffect, useMemo, useRef, useState } from "react";

import { MarketWsClient } from "../services/marketWsClient";
import type { Interval } from "../types/market";

export interface WatchlistRow {
  symbol: string;
  price: number;
  direction: "up" | "down" | "none";
  flashing: boolean;
}

interface UseWatchlistTicksParams {
  symbols: string[];
  interval: Interval;
}

export function useWatchlistTicks({ symbols, interval }: UseWatchlistTicksParams): WatchlistRow[] {
  const [rows, setRows] = useState<WatchlistRow[]>(
    symbols.map((symbol) => ({ symbol: symbol.toLowerCase(), price: 0, direction: "none", flashing: false }))
  );
  const wsClient = useMemo(() => new MarketWsClient(), []);
  const unsubscribesRef = useRef<Array<() => void>>([]);
  const timersRef = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    setRows(
      symbols.map((symbol) => ({ symbol: symbol.toLowerCase(), price: 0, direction: "none", flashing: false }))
    );

    wsClient.connect({ symbols, intervals: [interval] });
    wsClient.updateWatchlist(symbols, [interval]);

    unsubscribesRef.current = symbols.map((symbol) => {
      const normalized = symbol.toLowerCase();
      return wsClient.subscribeTick({
        symbol: normalized,
        onTick: (tick) => {
          setRows((current) =>
            current.map((row) => {
              if (row.symbol !== tick.symbol) {
                return row;
              }

              const direction: "up" | "down" | "none" =
                row.price === 0 ? "none" : tick.price > row.price ? "up" : tick.price < row.price ? "down" : "none";

              const existingTimer = timersRef.current.get(row.symbol);
              if (existingTimer !== undefined) {
                window.clearTimeout(existingTimer);
              }
              const timerId = window.setTimeout(() => {
                setRows((nextRows) =>
                  nextRows.map((nextRow) =>
                    nextRow.symbol === row.symbol ? { ...nextRow, flashing: false } : nextRow
                  )
                );
              }, 150);
              timersRef.current.set(row.symbol, timerId);

              return {
                ...row,
                price: tick.price,
                direction,
                flashing: direction !== "none",
              };
            })
          );
        },
      });
    });

    return () => {
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
