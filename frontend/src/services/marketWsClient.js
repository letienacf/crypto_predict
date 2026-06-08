export class MarketWsClient {
    ws = null;
    sendWhenReady(payload) {
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
    connect({ symbols, intervals = [], baseUrl = "/ws/market" }) {
        if (this.ws !== null) {
            return;
        }
        const url = new URL(baseUrl, window.location.origin);
        url.searchParams.set("symbols", symbols.map((value) => value.toLowerCase()).join(","));
        url.searchParams.set("intervals", intervals.map((value) => value.toLowerCase()).join(","));
        this.ws = new WebSocket(url.toString());
        this.sendWhenReady({ action: "set_watchlist", symbols, intervals });
    }
    updateWatchlist(symbols, intervals = []) {
        this.sendWhenReady({ action: "set_watchlist", symbols, intervals });
    }
    subscribe(subscription) {
        if (this.ws === null) {
            throw new Error("WebSocket is not connected");
        }
        const handler = (event) => {
            let parsed;
            try {
                parsed = JSON.parse(event.data);
            }
            catch {
                return;
            }
            const candidate = parsed;
            if (candidate.event_type === undefined ||
                candidate.symbol !== subscription.symbol ||
                candidate.interval !== subscription.interval) {
                return;
            }
            subscription.onKline(candidate);
        };
        this.ws.addEventListener("message", handler);
        return () => {
            this.ws?.removeEventListener("message", handler);
        };
    }
    subscribeTick(subscription) {
        if (this.ws === null) {
            throw new Error("WebSocket is not connected");
        }
        const handler = (event) => {
            let parsed;
            try {
                parsed = JSON.parse(event.data);
            }
            catch {
                return;
            }
            const candidate = parsed;
            if (candidate.event_type !== "trade.tick" || candidate.symbol !== subscription.symbol) {
                return;
            }
            subscription.onTick(candidate);
        };
        this.ws.addEventListener("message", handler);
        return () => {
            this.ws?.removeEventListener("message", handler);
        };
    }
    close() {
        if (this.ws !== null) {
            this.ws.close();
            this.ws = null;
        }
    }
}
