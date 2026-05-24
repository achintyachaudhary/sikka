import type { ChartResponse, ChartTimeframe } from "./types/chart";
import type {
  IpoBatchFetchResponse,
  IpoLlmResearchResponse,
  IpoLlmStatusResponse,
} from "./types/ipoResearch";
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

export async function fetchIpoLlmStatus(
  symbols: string[],
): Promise<IpoLlmStatusResponse> {
  if (symbols.length === 0) {
    return { statuses: [] };
  }
  const params = new URLSearchParams({
    symbols: symbols.join(","),
  });
  const res = await fetch(`/api/ipo/llm-research/status?${params}`);
  if (!res.ok) {
    throw new Error(`IPO status failed (${res.status})`);
  }
  return res.json() as Promise<IpoLlmStatusResponse>;
}

export async function batchFetchIpoLlmResearch(
  items: { symbol: string; company_name?: string | null }[],
): Promise<IpoBatchFetchResponse> {
  const res = await fetch("/api/ipo/llm-research/batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      items: items.map((i) => ({
        symbol: i.symbol,
        company_name: i.company_name ?? null,
      })),
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `Batch IPO fetch failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json() as Promise<IpoBatchFetchResponse>;
}

export async function fetchIpoLlmResearch(
  symbol: string,
): Promise<IpoLlmResearchResponse> {
  const encoded = encodeURIComponent(symbol);
  const res = await fetch(`/api/ipo/${encoded}/llm-research`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `IPO research not found (${res.status})`;
    throw new Error(detail);
  }
  return res.json() as Promise<IpoLlmResearchResponse>;
}

export async function generateIpoLlmResearch(
  symbol: string,
  options?: { companyName?: string; refresh?: boolean },
): Promise<IpoLlmResearchResponse> {
  const encoded = encodeURIComponent(symbol);
  const params = new URLSearchParams();
  if (options?.companyName) {
    params.set("company_name", options.companyName);
  }
  if (options?.refresh) {
    params.set("refresh", "true");
  }
  const qs = params.toString();
  const res = await fetch(
    `/api/ipo/${encoded}/llm-research${qs ? `?${qs}` : ""}`,
    { method: "POST" },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `IPO LLM request failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json() as Promise<IpoLlmResearchResponse>;
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

export async function fetchStockChart(
  symbol: string,
  timeframe: ChartTimeframe,
): Promise<ChartResponse> {
  const encoded = encodeURIComponent(symbol);
  const res = await fetch(`/api/stock/${encoded}/chart?timeframe=${timeframe}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `Chart fetch failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json() as Promise<ChartResponse>;
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

export async function refreshStockData(
  symbol: string,
): Promise<StockInsightsResponse> {
  const encoded = encodeURIComponent(symbol);
  const res = await fetch(`/api/refresh/stock/${encoded}`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`Refresh failed (${res.status})`);
  }
  return res.json() as Promise<StockInsightsResponse>;
}

export interface WidgetItem {
  widget_type: string;
  size: "sm" | "md" | "lg";
  position: number;
  config: Record<string, unknown>;
}

export interface DashboardLayout {
  widgets: (WidgetItem & { id?: number })[];
}

export async function fetchDashboardLayout(): Promise<DashboardLayout> {
  const res = await fetch("/api/dashboard/layout");
  if (!res.ok) throw new Error(`Layout fetch failed (${res.status})`);
  return res.json() as Promise<DashboardLayout>;
}

export async function saveDashboardLayout(widgets: WidgetItem[]): Promise<void> {
  const res = await fetch("/api/dashboard/layout", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ widgets }),
  });
  if (!res.ok) throw new Error(`Layout save failed (${res.status})`);
}

export async function fetchIndexSummary() {
  const res = await fetch("/api/widgets/index-summary");
  if (!res.ok) throw new Error("Index summary failed");
  return res.json();
}

export async function fetchMarketIndices(refresh = false) {
  const params = refresh ? "?refresh=true" : "";
  const res = await fetch(`/api/market-indices${params}`);
  if (!res.ok) throw new Error(`Market indices failed (${res.status})`);
  return res.json();
}

export async function fetchMarketIndexChart(indexId: string) {
  const res = await fetch(`/api/market-indices/${encodeURIComponent(indexId)}/chart`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : `Index chart failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchTopMovers() {
  const res = await fetch("/api/widgets/top-movers");
  if (!res.ok) throw new Error("Top movers failed");
  return res.json();
}
