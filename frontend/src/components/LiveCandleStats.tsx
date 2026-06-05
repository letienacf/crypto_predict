import type { KlineItem } from "../types/market";
import { useServerTime } from "../hooks/useServerTime";

interface LiveCandleStatsProps {
  symbol: string;
  interval: string;
  latestCandle: KlineItem | null;
}

function formatCountdown(totalSeconds: number): string {
  const seconds = Math.max(totalSeconds, 0);
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}

export function LiveCandleStats({ symbol, interval, latestCandle }: LiveCandleStatsProps): JSX.Element {
  const { nowMs, offsetMs } = useServerTime();

  const closeMs = latestCandle === null ? 0 : new Date(latestCandle.timestamp).getTime();
  const countdownSec = closeMs > 0 ? Math.floor((closeMs - nowMs) / 1000) : 0;

  return (
    <section style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 8, padding: 12 }}>
      <h2 style={{ color: "#E5E7EB", marginTop: 0 }}>Live Candle Stats</h2>
      <p style={{ color: "#9CA3AF", marginTop: 0 }}>
        {symbol.toUpperCase()} {interval} | Server offset: {offsetMs} ms
      </p>

      {latestCandle === null ? (
        <p style={{ color: "#9CA3AF" }}>No active candle yet.</p>
      ) : (
        <div style={{ display: "grid", gap: 6, color: "#E5E7EB", fontVariantNumeric: "tabular-nums" }}>
          <div>O: {latestCandle.open.toFixed(4)}</div>
          <div>H: {latestCandle.high.toFixed(4)}</div>
          <div>L: {latestCandle.low.toFixed(4)}</div>
          <div>C: {latestCandle.close.toFixed(4)}</div>
          <div>V: {latestCandle.volume.toFixed(4)}</div>
          <div style={{ color: "#FCD535", fontWeight: 700 }}>
            Countdown: {formatCountdown(countdownSec)}
          </div>
        </div>
      )}
    </section>
  );
}
