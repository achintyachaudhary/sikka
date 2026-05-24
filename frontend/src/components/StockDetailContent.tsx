import { useEffect, useState } from "react";
import { fetchStockInsights } from "../api";
import type { StockInsightsResponse } from "../types";
import FinancialChart from "./FinancialChart";
import ShareholdingChart from "./ShareholdingChart";

function fmtCapCr(v: number | null): string {
  if (v == null) return "—";
  if (v >= 100_000) return `₹${(v / 100_000).toFixed(2)} L Cr`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}k Cr`;
  return `₹${v.toFixed(0)} Cr`;
}

interface StockDetailContentProps {
  symbol: string;
  yfSymbol?: string | null;
}

export default function StockDetailContent({
  symbol,
  yfSymbol,
}: StockDetailContentProps) {
  const [data, setData] = useState<StockInsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSymbol = yfSymbol || symbol;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);

    fetchStockInsights(fetchSymbol)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fetchSymbol]);

  if (loading) {
    return <p className="panel-loading">Loading company details…</p>;
  }

  if (error) {
    return <p className="panel-error">{error}</p>;
  }

  if (!data) return null;

  return (
    <>
      <div className="detail-meta">
        <div className="detail-meta-row">
          {data.market_cap_category && (
            <span className={`meta-badge cap-${data.market_cap_category.split(" ")[0].toLowerCase()}`}>
              {data.market_cap_category}
            </span>
          )}
          {data.sector && (
            <span className="meta-badge sector">{data.sector}</span>
          )}
          {data.industry && (
            <span className="meta-badge industry">{data.industry}</span>
          )}
        </div>
        {data.market_cap_cr != null && (
          <p className="meta-cap-value">
            Market cap: {fmtCapCr(data.market_cap_cr)}
          </p>
        )}
      </div>

      <div className="detail-grid">
        <ShareholdingChart periods={data.shareholding} />
        <FinancialChart
          quarterly={data.financials_quarterly}
          yearly={data.financials_yearly}
          revenueGrowthYoy={data.revenue_growth_yoy_pct}
          revenueCagr3y={data.revenue_cagr_3y_pct}
          profitGrowthYoy={data.profit_growth_yoy_pct}
          profitCagr3y={data.profit_cagr_3y_pct}
        />
      </div>
    </>
  );
}
