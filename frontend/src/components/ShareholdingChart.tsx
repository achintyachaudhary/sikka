import { useState } from "react";
import type { ShareholdingPeriod } from "../types";

const BAR_ITEMS = [
  { key: "fii_holding_pct" as const, label: "Foreign Institutions" },
  { key: "promoter_holding_pct" as const, label: "Promoters" },
  { key: "dii_holding_pct" as const, label: "Domestic Institutions" },
  { key: "retail_and_others_pct" as const, label: "Retail And Others" },
];

interface ShareholdingChartProps {
  periods: ShareholdingPeriod[];
}

export default function ShareholdingChart({ periods }: ShareholdingChartProps) {
  const [activeIdx, setActiveIdx] = useState(Math.max(0, periods.length - 1));

  if (!periods.length) {
    return <p className="panel-empty">Shareholding data not available.</p>;
  }

  const period = periods[activeIdx] ?? periods[periods.length - 1];

  return (
    <div className="insight-panel">
      <h3 className="panel-title">Shareholding Pattern</h3>
      <div className="period-tabs">
        {periods.map((p, i) => (
          <button
            key={p.as_of}
            type="button"
            className={`period-tab${i === activeIdx ? " active" : ""}`}
            onClick={() => setActiveIdx(i)}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div className="holding-bars">
        {BAR_ITEMS.map(({ key, label }) => {
          const pct = period[key];
          if (pct == null) return null;
          return (
            <div key={key} className="holding-bar-row">
              <span className="holding-label">{label}</span>
              <div className="holding-bar-track">
                <div
                  className="holding-bar-fill"
                  style={{ width: `${Math.min(pct, 100)}%` }}
                />
              </div>
              <span className="holding-pct">{pct.toFixed(2)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
