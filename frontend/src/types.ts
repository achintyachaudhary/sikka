export interface StockSignal {
  symbol: string;
  price: number;
  change_5d_pct: number | null;
  change_20d_pct: number | null;
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  sma_20: number | null;
  sma_50: number | null;
  score: number;
  signals: string[];
  warnings: string[];
  trend: string;
}

export interface ScanResponse {
  scanned_at: string;
  index: string;
  index_label: string;
  total_scanned: number;
  total_matched: number;
  min_score: number;
  results: StockSignal[];
}

export interface IndexOption {
  id: string;
  label: string;
  description: string;
  slow_scan: boolean;
}

export interface IndicesResponse {
  indices: IndexOption[];
}
