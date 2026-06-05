export type Interval = "1m" | "5m" | "15m" | "1h" | "4h" | "1d" | "1w";

export interface KlineItem {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface KlineResponse {
  status: "success";
  data: KlineItem[];
}

export interface LiveKlineEvent {
  event_type: "kline.partial" | "kline.closed";
  event_version: 1;
  symbol: string;
  interval: Interval;
  open_time: string;
  close_time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  is_closed: boolean;
}

export interface LiveTradeTickEvent {
  event_type: "trade.tick";
  event_version: 1;
  exchange: "binance";
  symbol: string;
  price: number;
  quantity: number;
  trade_time: string;
  ingested_at: string;
}
