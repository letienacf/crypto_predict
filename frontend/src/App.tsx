import { LiveCandleStats } from "./components/LiveCandleStats";
import { RealtimeCandlestickChart } from "./components/RealtimeCandlestickChart";
import { WatchlistPanel } from "./components/WatchlistPanel";
import { useHybridKlines } from "./hooks/useHybridKlines";

export function App(): JSX.Element {
  const symbol = "btcusdt";
  const interval = "1m" as const;
  const { klines, isLoading, error } = useHybridKlines({ symbol, interval, limit: 300 });
  const latestCandle = klines.length > 0 ? klines[klines.length - 1] : null;

  return (
    <main style={{ fontFamily: "ui-sans-serif, sans-serif", padding: 24, background: "#030712", minHeight: "100vh" }}>
      <h1 style={{ color: "#E5E7EB", marginTop: 0 }}>Crypto Predict Sprint 3</h1>

      {isLoading ? <p style={{ color: "#9CA3AF" }}>Loading chart data...</p> : null}
      {error !== null ? <p style={{ color: "#FCA5A5" }}>Error: {error}</p> : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 3fr) minmax(260px, 1fr)",
          gap: 16,
          alignItems: "start",
        }}
      >
        <RealtimeCandlestickChart
          klines={klines}
          title={`Realtime Candles ${symbol.toUpperCase()} ${interval}`}
        />
        <div style={{ display: "grid", gap: 16 }}>
          <WatchlistPanel symbols={["btcusdt", "ethusdt", "bnbusdt"]} interval={interval} />
          <LiveCandleStats symbol={symbol} interval={interval} latestCandle={latestCandle} />
        </div>
      </div>
    </main>
  );
}
