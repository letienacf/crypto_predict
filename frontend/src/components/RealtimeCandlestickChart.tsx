import { useEffect, useRef } from "react";
import {
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";

import type { KlineItem } from "../types/market";

interface RealtimeCandlestickChartProps {
  klines: KlineItem[];
  title: string;
}

function toCandle(kline: KlineItem): CandlestickData {
  return {
    time: Math.floor(new Date(kline.timestamp).getTime() / 1000) as UTCTimestamp,
    open: kline.open,
    high: kline.high,
    low: kline.low,
    close: kline.close,
  };
}

export function RealtimeCandlestickChart({ klines, title }: RealtimeCandlestickChartProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (containerRef.current === null || chartRef.current !== null) {
      return;
    }

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#111827" },
        textColor: "#D1D5DB",
      },
      grid: {
        vertLines: { color: "#1F2937" },
        horzLines: { color: "#1F2937" },
      },
      width: containerRef.current.clientWidth,
      height: 420,
      rightPriceScale: {
        borderColor: "#374151",
      },
      timeScale: {
        borderColor: "#374151",
      },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#0ECB81",
      downColor: "#F6465D",
      borderVisible: false,
      wickUpColor: "#0ECB81",
      wickDownColor: "#F6465D",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current !== null && chartRef.current !== null) {
        chartRef.current.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (series === null || klines.length === 0) {
      return;
    }

    const candles = klines.map(toCandle);
    series.setData(candles);
  }, [klines]);

  return (
    <section style={{ background: "#111827", border: "1px solid #1F2937", borderRadius: 8, padding: 12 }}>
      <h2 style={{ color: "#E5E7EB", marginTop: 0, marginBottom: 12 }}>{title}</h2>
      <div ref={containerRef} style={{ width: "100%", minHeight: 420 }} />
    </section>
  );
}
