import { useEffect, useState } from "react";
import { fetchIndexSummary } from "../../api";

interface IndexEntry {
  name: string;
  value: number;
  change_pct: number;
}

export default function IndexSummaryWidget() {
  const [indices, setIndices] = useState<IndexEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchIndexSummary()
      .then((d) => setIndices(d.indices ?? []))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="widget-loading">Loading…</div>;
  if (error) return <div className="widget-error">{error}</div>;
  if (!indices.length) return <div className="widget-empty">No index data</div>;

  return (
    <div className="index-summary-list">
      {indices.map((idx) => (
        <div key={idx.name} className="index-row">
          <span className="index-name">{idx.name}</span>
          <span className="index-value">{idx.value.toLocaleString()}</span>
          <span className={`index-chg ${idx.change_pct >= 0 ? "pct-pos" : "pct-neg"}`}>
            {idx.change_pct > 0 ? "+" : ""}
            {idx.change_pct.toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  );
}
