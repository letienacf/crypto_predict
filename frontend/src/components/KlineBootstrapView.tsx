import type { Interval } from "../types/market";
import { useHybridKlines } from "../hooks/useHybridKlines";

interface KlineBootstrapViewProps {
  symbol: string;
  interval: Interval;
}

export function KlineBootstrapView({ symbol, interval }: KlineBootstrapViewProps): JSX.Element {
  const { klines, isLoading, error } = useHybridKlines({ symbol, interval, limit: 200 });

  if (isLoading) {
    return <p>Loading historical candles...</p>;
  }

  if (error !== null) {
    return <p>Error: {error}</p>;
  }

  const last = klines[klines.length - 1];

  return (
    <section>
      <h2>
        Hybrid stream active for {symbol.toUpperCase()} {interval}
      </h2>
      <p>Total candles in memory: {klines.length}</p>
      {last !== undefined ? (
        <p>
          Last close: {last.close} | High: {last.high} | Low: {last.low}
        </p>
      ) : (
        <p>No data yet.</p>
      )}
    </section>
  );
}
