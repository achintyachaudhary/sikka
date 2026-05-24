import { useEffect, useState } from "react";
import { fetchScan } from "../../api";
import type { StockSignal } from "../../types";
import { tradingViewChartUrl, displaySymbol } from "../../utils/tradingView";

interface Props {
  size: "sm" | "md" | "lg";
}

const LIMIT_MAP = { sm: 5, md: 8, lg: 15 };

export default function BullishStocksWidget({ size }: Props) {
  const [stocks, setStocks] = useState<StockSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchScan(4, "nifty50")
      .then((d) => setStocks(d.results.slice(0, LIMIT_MAP[size])))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [size]);

  if (loading) return <div className="widget-loading">Loading…</div>;
  if (error) return <div className="widget-error">{error}</div>;
  if (!stocks.length) return <div className="widget-empty">No bullish signals found</div>;

  return (
    <div className="mini-list">
      {stocks.map((s) => (
        <div key={s.symbol} className="mini-row">
          <a
            href={tradingViewChartUrl(s.symbol)}
            target="_blank"
            rel="noopener noreferrer"
            className="mini-symbol symbol-link"
          >
            {displaySymbol(s.symbol)}
          </a>
          <span className="mini-price">₹{s.price.toLocaleString()}</span>
          <span
            className={`mini-chg ${s.change_5d_pct != null && s.change_5d_pct >= 0 ? "pct-pos" : "pct-neg"}`}
          >
            {s.change_5d_pct != null ? `${s.change_5d_pct > 0 ? "+" : ""}${s.change_5d_pct.toFixed(1)}%` : "—"}
          </span>
        </div>
      ))}
    </div>
  );
}
