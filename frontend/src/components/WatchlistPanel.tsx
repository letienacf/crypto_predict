import { useWatchlistTicks } from "../hooks/useWatchlistTicks";
import type { Interval } from "../types/market";

interface WatchlistPanelProps {
  symbols: string[];
  interval: Interval;
}

export function WatchlistPanel({ symbols, interval }: WatchlistPanelProps): JSX.Element {
  const rows = useWatchlistTicks({ symbols, interval });

  return (
    <section style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 8, padding: 12 }}>
      <h2 style={{ color: "#E5E7EB", marginTop: 0 }}>Watchlist</h2>
      <div style={{ display: "grid", gap: 8 }}>
        {rows.map((row) => {
          const color = row.direction === "up" ? "#0ECB81" : row.direction === "down" ? "#F6465D" : "#E5E7EB";
          const background = row.flashing
            ? row.direction === "up"
              ? "rgba(14, 203, 129, 0.18)"
              : "rgba(246, 70, 93, 0.18)"
            : "transparent";

          return (
            <div
              key={row.symbol}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 10px",
                borderRadius: 6,
                transition: "background-color 150ms ease",
                backgroundColor: background,
              }}
            >
              <strong style={{ color: "#9CA3AF" }}>{row.symbol.toUpperCase()}</strong>
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
