import type { IndicesResponse, IpoTrackResponse, ScanResponse, StockInsightsResponse } from "./types";

export async function fetchIndices(): Promise<IndicesResponse> {
  const res = await fetch("/api/indices");
  if (!res.ok) {
    throw new Error(`Failed to load indices (${res.status})`);
  }
  return res.json() as Promise<IndicesResponse>;
}

export async function fetchScan(
  minScore: number,
  index: string,
  refresh = false,
): Promise<ScanResponse> {
  const params = new URLSearchParams({
    min_score: String(minScore),
    limit: "100",
    index,
  });
  if (refresh) {
    params.set("refresh", "true");
  }

  const res = await fetch(`/api/scan?${params}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `Scan failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json() as Promise<ScanResponse>;
}

export async function fetchIpos(
  months: 1 | 2,
  refresh = false,
): Promise<IpoTrackResponse> {
  const params = new URLSearchParams({ months: String(months) });
  if (refresh) {
    params.set("refresh", "true");
  }

  const res = await fetch(`/api/ipo?${params}`);
  if (!res.ok) {
    throw new Error(`IPO fetch failed (${res.status})`);
  }
  return res.json() as Promise<IpoTrackResponse>;
}

export async function fetchStockInsights(
  symbol: string,
): Promise<StockInsightsResponse> {
  const encoded = encodeURIComponent(symbol);
  const res = await fetch(`/api/stock/${encoded}/insights`);
  if (!res.ok) {
    throw new Error(`Insights failed (${res.status})`);
  }
  return res.json() as Promise<StockInsightsResponse>;
}
