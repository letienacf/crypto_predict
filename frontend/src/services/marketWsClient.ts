import type { Interval, LiveKlineEvent, LiveTradeTickEvent } from "../types/market";

interface Subscription {
  symbol: string;
  interval: Interval;
  onKline: (event: LiveKlineEvent) => void;
}

interface TickSubscription {
  symbol: string;
  onTick: (event: LiveTradeTickEvent) => void;
}

interface ConnectParams {
  symbols: string[];
  intervals?: Interval[];
  baseUrl?: string;
}

export class MarketWsClient {
  private ws: WebSocket | null = null;

  private sendWhenReady(payload: unknown): void {
    if (this.ws === null) {
      return;
    }

    const encoded = JSON.stringify(payload);
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(encoded);
      return;
    }

    const handler = () => {
      this.ws?.send(encoded);
      this.ws?.removeEventListener("open", handler);
    };
    this.ws.addEventListener("open", handler);
  }

  connect({ symbols, intervals = [], baseUrl = "ws://localhost:8000/ws/market" }: ConnectParams): void {
    if (this.ws !== null) {
      return;
    }

    const url = new URL(baseUrl);
    url.searchParams.set("symbols", symbols.map((value) => value.toLowerCase()).join(","));
    url.searchParams.set("intervals", intervals.map((value) => value.toLowerCase()).join(","));
    this.ws = new WebSocket(url.toString());

    this.sendWhenReady({ action: "set_watchlist", symbols, intervals });
  }

  updateWatchlist(symbols: string[], intervals: Interval[] = []): void {
    this.sendWhenReady({ action: "set_watchlist", symbols, intervals });
  }

  subscribe(subscription: Subscription): () => void {
    if (this.ws === null) {
      throw new Error("WebSocket is not connected");
    }

    const handler = (event: MessageEvent<string>) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }

      const candidate = parsed as Partial<LiveKlineEvent>;
      if (
        candidate.event_type === undefined ||
        candidate.symbol !== subscription.symbol ||
        candidate.interval !== subscription.interval
      ) {
        return;
      }

      subscription.onKline(candidate as LiveKlineEvent);
    };

    this.ws.addEventListener("message", handler);
    return () => {
      this.ws?.removeEventListener("message", handler);
    };
  }

  subscribeTick(subscription: TickSubscription): () => void {
    if (this.ws === null) {
      throw new Error("WebSocket is not connected");
    }

    const handler = (event: MessageEvent<string>) => {
      let parsed: unknown;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }

      const candidate = parsed as Partial<LiveTradeTickEvent>;
      if (candidate.event_type !== "trade.tick" || candidate.symbol !== subscription.symbol) {
        return;
      }

      subscription.onTick(candidate as LiveTradeTickEvent);
    };

    this.ws.addEventListener("message", handler);
    return () => {
      this.ws?.removeEventListener("message", handler);
    };
  }

  close(): void {
    if (this.ws !== null) {
      this.ws.close();
      this.ws = null;
    }
  }
}
