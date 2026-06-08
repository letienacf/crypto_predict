import { useMemo } from "react";

interface OrderBookPanelProps {
  lastPrice: number;
}

interface OrderBookRow {
  price: number;
  amount: number;
  total: number;
  depth: number;
}

function formatPrice(value: number): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatAmount(value: number): string {
  return value.toLocaleString("en-US", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

function buildRows(lastPrice: number, isAsk: boolean): OrderBookRow[] {
  const rows: OrderBookRow[] = [];
  for (let i = 1; i <= 8; i += 1) {
    const step = 2 + i * 0.8;
    const price = isAsk ? lastPrice + step : lastPrice - step;
    const amount = 0.2 + i * 0.08;
    rows.push({
      price,
      amount,
      total: price * amount,
      depth: 14 + i * 6,
    });
  }
  return rows;
}

export function OrderBookPanel({ lastPrice }: OrderBookPanelProps): JSX.Element {
  const asks = useMemo(() => buildRows(lastPrice, true).reverse(), [lastPrice]);
  const bids = useMemo(() => buildRows(lastPrice, false), [lastPrice]);

  return (
    <section className="panel panel--orderbook panel--orderbook-bottom">
      <div className="panel__header">
        <h2>Order Book</h2>
        <span>Depth 24</span>
      </div>

      <div className="orderbook-head orderbook-head--split">
        <span className="text-up">Bids</span>
        <span className="orderbook-head__price">Last {formatPrice(lastPrice)}</span>
        <span className="text-down">Asks</span>
      </div>

      <div className="orderbook-grid">
        <div className="orderbook-column orderbook-column--bid">
          {bids.map((row) => (
            <div key={`bid-${row.price}`} className="orderbook-row orderbook-row--bid">
              <div className="orderbook-row__depth" style={{ width: `${row.depth}%` }} />
              <span className="mono text-up">{formatPrice(row.price)}</span>
              <span className="mono">{formatAmount(row.amount)}</span>
              <span className="mono">{formatPrice(row.total)}</span>
            </div>
          ))}
        </div>

        <div className="orderbook-column orderbook-column--ask">
          {asks.map((row) => (
            <div key={`ask-${row.price}`} className="orderbook-row orderbook-row--ask">
              <div className="orderbook-row__depth" style={{ width: `${row.depth}%` }} />
              <span className="mono text-down">{formatPrice(row.price)}</span>
              <span className="mono">{formatAmount(row.amount)}</span>
              <span className="mono">{formatPrice(row.total)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
