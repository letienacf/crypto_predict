import type { Interval, KlineResponse } from "../types/market";

const DEFAULT_BASE_URL = "http://localhost:8000";

export async function fetchHistoricalKlines(
  symbol: string,
  interval: Interval,
  limit = 1000,
  baseUrl = DEFAULT_BASE_URL
): Promise<KlineResponse> {
  const params = new URLSearchParams({
    symbol: symbol.toLowerCase(),
    interval,
    limit: String(limit),
  });

  const response = await fetch(`${baseUrl}/api/v1/market/klines?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch klines, status=${response.status}`);
  }

  const payload = (await response.json()) as KlineResponse;
  return payload;
}
