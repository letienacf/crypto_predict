import { useEffect, useMemo, useState } from "react";

import { LiveCandleStats } from "./components/LiveCandleStats";
import { OrderBookPanel } from "./components/OrderBookPanel";
import { RealtimeCandlestickChart } from "./components/RealtimeCandlestickChart";
import { WatchlistPanel } from "./components/WatchlistPanel";
import { useHybridKlines } from "./hooks/useHybridKlines";
import { useServerTime } from "./hooks/useServerTime";
import type { Interval } from "./types/market";

const AVAILABLE_SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt", "solusdt"] as const;
const AVAILABLE_INTERVALS: Interval[] = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"];
type MarketSymbol = (typeof AVAILABLE_SYMBOLS)[number];

const USER_PREFERENCES_STORAGE_KEY = "crypto_predict.user_preferences.v1";

interface UserPreferences {
  symbol?: string;
  interval?: string;
}

function isMarketSymbol(value: string): value is MarketSymbol {
  return (AVAILABLE_SYMBOLS as readonly string[]).includes(value);
}

function isInterval(value: string): value is Interval {
  return (AVAILABLE_INTERVALS as readonly string[]).includes(value);
}

function loadUserPreferences(): { symbol: MarketSymbol; interval: Interval } {
  const fallback = { symbol: "btcusdt" as MarketSymbol, interval: "5m" as Interval };
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(USER_PREFERENCES_STORAGE_KEY);
    if (raw === null) {
      return fallback;
    }

    const parsed = JSON.parse(raw) as UserPreferences;
    const nextSymbol = typeof parsed.symbol === "string" && isMarketSymbol(parsed.symbol) ? parsed.symbol : fallback.symbol;
    const nextInterval = typeof parsed.interval === "string" && isInterval(parsed.interval) ? parsed.interval : fallback.interval;
    return { symbol: nextSymbol, interval: nextInterval };
  } catch {
    return fallback;
  }
}

export function App(): JSX.Element {
  const [initialPreferences] = useState(loadUserPreferences);
  const [symbol, setSymbol] = useState<MarketSymbol>(initialPreferences.symbol);
  const [interval, setInterval] = useState<Interval>(initialPreferences.interval);
  const { nowMs, offsetMs } = useServerTime();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const preferences: UserPreferences = { symbol, interval };
    window.localStorage.setItem(USER_PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
  }, [symbol, interval]);

  const { klines, isLoading, error } = useHybridKlines({ symbol, interval, limit: 1000, nowMs });
  const latestCandle = klines.length > 0 ? klines[klines.length - 1] : null;
  const previousCandle = klines.length > 1 ? klines[klines.length - 2] : null;

  const changePercent = useMemo(() => {
    if (latestCandle === null || previousCandle === null || previousCandle.close === 0) {
      return 0;
    }

    return ((latestCandle.close - previousCandle.close) / previousCandle.close) * 100;
  }, [latestCandle, previousCandle]);

  const priceDirection = changePercent > 0 ? "up" : changePercent < 0 ? "down" : "flat";

  const lastPriceText = latestCandle === null ? "--" : latestCandle.close.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <main className="app-shell">
      <header className="terminal-header">
        <div className="terminal-header__left">
          <div className="brand">CRYPTO PREDICT PRO</div>
          <div className="market-title">
            <strong>{symbol.toUpperCase().replace("USDT", "/USDT")}</strong>
            <span>{interval}</span>
          </div>
          <div className="market-price">
            <strong className={priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : ""}>
              {lastPriceText}
            </strong>
            <span className={priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : ""}>
              {priceDirection === "up" ? "+" : ""}
              {changePercent.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="terminal-header__right">
          <span className={error !== null ? "status status--error" : isLoading ? "status" : "status status--live"}>
            {error !== null ? "Issue" : isLoading ? "Syncing" : "Live"}
          </span>
        </div>
      </header>

      <section className="terminal-workspace">
        <aside className="left-tools">
          <button type="button" title="Crosshair">⌖</button>
          <button type="button" title="Trendline">／</button>
          <button type="button" title="Fib">ƒx</button>
          <button type="button" title="Brush">✎</button>
          <button type="button" title="Settings">⚙</button>
        </aside>

        <section className="chart-zone">
          <div className="chart-toolbar">
            <div className="pill-row" role="tablist" aria-label="Timeframe selector">
              {AVAILABLE_INTERVALS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={item === interval ? "pill pill--active" : "pill"}
                  onClick={() => setInterval(item)}
                >
                  {item}
                </button>
              ))}
            </div>

            <div className="chart-toolbar__actions">
              <button type="button" className="ghost-button">Indicators</button>
              <button type="button" className="ghost-button">Compare</button>
              <button type="button" className="ghost-button">Alert</button>
            </div>
          </div>

          <div className="chart-stage panel">
            <div className="chart-stage__stats mono">
              <span>O {latestCandle?.open.toFixed(2) ?? "--"}</span>
              <span>H {latestCandle?.high.toFixed(2) ?? "--"}</span>
              <span>L {latestCandle?.low.toFixed(2) ?? "--"}</span>
              <span className={priceDirection === "up" ? "text-up" : priceDirection === "down" ? "text-down" : ""}>
                C {latestCandle?.close.toFixed(2) ?? "--"}
              </span>
            </div>
            <RealtimeCandlestickChart klines={klines} />
          </div>

          <OrderBookPanel lastPrice={latestCandle?.close ?? 10000} />
        </section>

        <aside className="right-sidebar">
          <WatchlistPanel
            symbols={AVAILABLE_SYMBOLS as unknown as string[]}
            interval={interval}
            activeSymbol={symbol}
            onSelectSymbol={setSymbol}
          />
          <LiveCandleStats symbol={symbol} interval={interval} latestCandle={latestCandle} nowMs={nowMs} offsetMs={offsetMs} />
        </aside>
      </section>
    </main>
  );
}
