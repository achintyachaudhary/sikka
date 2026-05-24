import { useEffect, useState } from "react";
import { fetchTopMovers } from "../../api";
import { tradingViewChartUrl, displaySymbol } from "../../utils/tradingView";

interface Mover {
  symbol: string;
  price: number;
  change_5d_pct: number | null;
}

interface TopMoversData {
  gainers: Mover[];
  losers: Mover[];
}

export default function TopMoversWidget() {
  const [data, setData] = useState<TopMoversData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"gainers" | "losers">("gainers");

  useEffect(() => {
    fetchTopMovers()
      .then((d) => setData(d))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="widget-loading">Loading…</div>;
  if (error) return <div className="widget-error">{error}</div>;
  if (!data) return <div className="widget-empty">No data</div>;

  const movers = tab === "gainers" ? data.gainers : data.losers;

  return (
    <div>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
        <button
          type="button"
          onClick={() => setTab("gainers")}
          style={{
            background: tab === "gainers" ? "var(--accent)" : "var(--surface)",
            color: tab === "gainers" ? "var(--accent-text)" : "var(--muted)",
            border: `1px solid var(--border)`,
            padding: "0.25rem 0.75rem",
            borderRadius: "999px",
            fontSize: "0.75rem",
            cursor: "pointer",
          }}
        >
          Gainers
        </button>
        <button
          type="button"
          onClick={() => setTab("losers")}
          style={{
            background: tab === "losers" ? "var(--red)" : "var(--surface)",
            color: tab === "losers" ? "#fff" : "var(--muted)",
            border: `1px solid var(--border)`,
            padding: "0.25rem 0.75rem",
            borderRadius: "999px",
            fontSize: "0.75rem",
            cursor: "pointer",
          }}
        >
          Losers
        </button>
      </div>
      <div className="mini-list">
        {movers.length === 0 && <div className="widget-empty">No data yet</div>}
        {movers.map((m) => (
          <div key={m.symbol} className="mini-row">
            <a
              href={tradingViewChartUrl(m.symbol)}
              target="_blank"
              rel="noopener noreferrer"
              className="mini-symbol symbol-link"
            >
              {displaySymbol(m.symbol)}
            </a>
            <span className="mini-price">₹{m.price.toLocaleString()}</span>
            <span className={`mini-chg ${(m.change_5d_pct ?? 0) >= 0 ? "pct-pos" : "pct-neg"}`}>
              {m.change_5d_pct != null
                ? `${m.change_5d_pct > 0 ? "+" : ""}${m.change_5d_pct.toFixed(1)}%`
                : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
