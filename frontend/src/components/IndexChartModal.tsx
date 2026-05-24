import { useEffect, useState } from "react";
import { fetchMarketIndexChart } from "../api";
import type { MarketIndexQuote } from "../types/marketIndex";
import type { OhlcBar } from "../types/chart";
import LightweightStockChart from "./LightweightStockChart";

interface IndexChartModalProps {
  index: MarketIndexQuote | null;
  onClose: () => void;
}

export default function IndexChartModal({ index, onClose }: IndexChartModalProps) {
  const [bars, setBars] = useState<OhlcBar[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!index) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [index, onClose]);

  useEffect(() => {
    if (!index) {
      setBars([]);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchMarketIndexChart(index.index_id)
      .then((res) => {
        if (!cancelled) setBars(res.bars);
      })
      .catch((err) => {
        if (!cancelled) {
          setBars([]);
          setError(err instanceof Error ? err.message : "Failed to load chart");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [index]);

  if (!index) return null;

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal-panel index-chart-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="index-chart-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          <div className="modal-title-wrap">
            <h2 id="index-chart-title">{index.display_name}</h2>
            <span className="index-chart-subtitle">1 year · daily</span>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>
        <div className="modal-body">
          {loading && <p className="panel-loading">Loading chart…</p>}
          {error && <p className="panel-error">{error}</p>}
          {!loading && !error && bars.length === 0 && (
            <p className="panel-empty">No chart data available.</p>
          )}
          {!loading && bars.length > 0 && (
            <LightweightStockChart bars={bars} height={400} />
          )}
        </div>
      </div>
    </div>
  );
}
