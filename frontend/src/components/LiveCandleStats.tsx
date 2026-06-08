import type { KlineItem } from "../types/market";

interface LiveCandleStatsProps {
  symbol: string;
  interval: string;
  latestCandle: KlineItem | null;
  nowMs: number;
  offsetMs: number;
}

function formatCountdown(totalSeconds: number): string {
  const seconds = Math.max(totalSeconds, 0);
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}

export function LiveCandleStats({ symbol, interval, latestCandle, nowMs, offsetMs }: LiveCandleStatsProps): JSX.Element {
  const closeMs = latestCandle === null ? 0 : new Date(latestCandle.timestamp).getTime();
  const countdownSec = closeMs > 0 ? Math.floor((closeMs - nowMs) / 1000) : 0;

  return (
    <section className="panel panel--stats">
      <div className="panel__header">
        <h2>Live Candle Stats</h2>
        <span>Server sync</span>
      </div>
      <p className="panel__meta">
        {symbol.toUpperCase()} {interval} | Server offset: {offsetMs} ms
      </p>

      {latestCandle === null ? (
        <p className="panel__empty">No active candle yet.</p>
      ) : (
        <div className="stats-grid">
          <div className="stats-item">
            <span>Open</span>
            <strong>{latestCandle.open.toFixed(4)}</strong>
          </div>
          <div className="stats-item">
            <span>High</span>
            <strong>{latestCandle.high.toFixed(4)}</strong>
          </div>
          <div className="stats-item">
            <span>Low</span>
            <strong>{latestCandle.low.toFixed(4)}</strong>
          </div>
          <div className="stats-item">
            <span>Close</span>
            <strong>{latestCandle.close.toFixed(4)}</strong>
          </div>
          <div className="stats-item stats-item--full">
            <span>Volume</span>
            <strong>{latestCandle.volume.toFixed(4)}</strong>
          </div>
          <div className="stats-item stats-item--full stats-item--countdown">
            <span>Countdown</span>
            <strong>{formatCountdown(countdownSec)}</strong>
          </div>
        </div>
      )}
    </section>
  );
}
