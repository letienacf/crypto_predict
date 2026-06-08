const DEFAULT_BASE_URL = "";
export async function fetchHistoricalKlines(symbol, interval, limit = 1000, baseUrl = DEFAULT_BASE_URL) {
    const params = new URLSearchParams({
        symbol: symbol.toLowerCase(),
        interval,
        limit: String(limit),
    });
    const response = await fetch(`${baseUrl}/api/v1/market/klines?${params.toString()}`);
    if (!response.ok) {
        throw new Error(`Failed to fetch klines, status=${response.status}`);
    }
    const payload = (await response.json());
    return payload;
}
