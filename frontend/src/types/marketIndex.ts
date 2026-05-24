import type { OhlcBar } from "./chart";

export interface MarketIndexQuote {
  index_id: string;
  display_name: string;
  yf_symbol: string;
  last_value: number | null;
  change_abs: number | null;
  change_pct: number | null;
  updated_at: string | null;
}

export interface MarketIndicesResponse {
  indices: MarketIndexQuote[];
}

export interface MarketIndexChartResponse {
  index_id: string;
  display_name: string;
  yf_symbol: string;
  timeframe: string;
  interval: string;
  bars: OhlcBar[];
}
