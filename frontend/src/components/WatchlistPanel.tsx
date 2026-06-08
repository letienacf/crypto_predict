import { useWatchlistTicks } from "../hooks/useWatchlistTicks";
import type { Interval } from "../types/market";

type MarketSymbol = "btcusdt" | "ethusdt" | "bnbusdt" | "solusdt";

interface WatchlistPanelProps {
  symbols: string[];
  interval: Interval;
  activeSymbol: MarketSymbol;
  onSelectSymbol: (symbol: MarketSymbol) => void;
}

export function WatchlistPanel({ symbols, interval, activeSymbol, onSelectSymbol }: WatchlistPanelProps): JSX.Element {
  const rows = useWatchlistTicks({ symbols, interval });

  return (
    <section className="panel panel--watchlist">
      <div className="panel__header">
        <h2>Watchlist</h2>
        <span>{interval}</span>
      </div>
      <div className="watchlist-hint">Click a symbol to load it into the main chart</div>
      <div className="watchlist-grid">
        {rows.map((row) => {
          const rowSymbol = row.symbol as MarketSymbol;
          const color = row.direction === "up" ? "#0ECB81" : row.direction === "down" ? "#F6465D" : "#E5E7EB";
          const background = row.flashing
            ? row.direction === "up"
              ? "rgba(14, 203, 129, 0.18)"
              : "rgba(246, 70, 93, 0.18)"
            : "transparent";
          const isActive = row.symbol === activeSymbol;

          return (
            <div
              key={row.symbol}
              className={isActive ? "watchlist-row watchlist-row--active" : "watchlist-row"}
              style={row.flashing ? { backgroundColor: background } : undefined}
              role="button"
              tabIndex={0}
              onClick={() => onSelectSymbol(rowSymbol)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectSymbol(rowSymbol);
                }
              }}
            >
              <strong style={{ color: isActive ? "#F9FAFB" : "#9CA3AF" }}>{row.symbol.toUpperCase()}</strong>
              <span style={{ color, fontVariantNumeric: "tabular-nums" }}>
                {row.price === 0 ? "--" : row.price.toFixed(4)}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
