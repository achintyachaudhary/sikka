import { useCallback, useEffect, useState } from "react";
import { fetchMarketIndices } from "../api";
import type { MarketIndexQuote } from "../types/marketIndex";
import IndexChartModal from "./IndexChartModal";

function fmtValue(v: number | null): string {
  if (v == null) return "—";
  return v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtChange(abs: number | null, pct: number | null): string {
  if (abs == null || pct == null) return "—";
  return `${abs.toFixed(2)} (${pct.toFixed(2)}%)`;
}

export default function MarketIndexTicker() {
  const [indices, setIndices] = useState<MarketIndexQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<MarketIndexQuote | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetchMarketIndices();
      setIndices(res.indices);
    } catch {
      setIndices([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const id = window.setInterval(() => void load(), 5 * 60 * 1000);
    return () => window.clearInterval(id);
  }, [load]);

  if (loading && indices.length === 0) {
    return <div className="market-index-ticker loading">Loading indices…</div>;
  }

  return (
    <>
      <div className="market-index-ticker" role="group" aria-label="Market indices">
        {indices.map((idx) => {
          const positive = (idx.change_pct ?? 0) >= 0;
          return (
            <button
              key={idx.index_id}
              type="button"
              className="market-index-item"
              onClick={() => setSelected(idx)}
              title={`View ${idx.display_name} 1Y chart`}
            >
              <span className="market-index-name">{idx.display_name}</span>
              <span className="market-index-value">{fmtValue(idx.last_value)}</span>
              <span className={`market-index-change ${positive ? "pct-pos" : "pct-neg"}`}>
                {fmtChange(idx.change_abs, idx.change_pct)}
              </span>
            </button>
          );
        })}
      </div>

      <IndexChartModal index={selected} onClose={() => setSelected(null)} />
    </>
  );
}
