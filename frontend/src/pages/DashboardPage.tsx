import { useCallback, useEffect, useState } from "react";
import {
  fetchDashboardLayout,
  saveDashboardLayout,
  type WidgetItem,
} from "../api";
import WidgetPicker from "../components/WidgetPicker";
import BullishStocksWidget from "../components/widgets/BullishStocksWidget";
import RecentIPOsWidget from "../components/widgets/RecentIPOsWidget";
import IndexSummaryWidget from "../components/widgets/IndexSummaryWidget";
import TopMoversWidget from "../components/widgets/TopMoversWidget";

type WidgetWithId = WidgetItem & { id?: number };

const WIDGET_LABELS: Record<string, string> = {
  bullish_stocks: "Bullish Stocks",
  recent_ipos: "Recent IPOs",
  index_summary: "Index Summary",
  top_movers: "Top Movers",
};

const WIDGET_ICONS: Record<string, string> = {
  bullish_stocks: "📊",
  recent_ipos: "🚀",
  index_summary: "📈",
  top_movers: "⚡",
};

function WidgetContent({
  widget,
}: {
  widget: WidgetWithId;
}) {
  switch (widget.widget_type) {
    case "bullish_stocks":
      return <BullishStocksWidget size={widget.size} />;
    case "recent_ipos":
      return <RecentIPOsWidget size={widget.size} />;
    case "index_summary":
      return <IndexSummaryWidget />;
    case "top_movers":
      return <TopMoversWidget />;
    default:
      return <div className="widget-empty">Unknown widget: {widget.widget_type}</div>;
  }
}

export default function DashboardPage() {
  const [widgets, setWidgets] = useState<WidgetWithId[]>([]);
  const [loading, setLoading] = useState(true);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchDashboardLayout()
      .then((data) => setWidgets(data.widgets as WidgetWithId[]))
      .catch(() => setWidgets([]))
      .finally(() => setLoading(false));
  }, []);

  const persistLayout = useCallback(async (updated: WidgetWithId[]) => {
    setSaving(true);
    try {
      await saveDashboardLayout(
        updated.map((w, i) => ({
          widget_type: w.widget_type,
          size: w.size,
          position: i,
          config: w.config ?? {},
        }))
      );
    } catch {
      // ignore save errors silently
    } finally {
      setSaving(false);
    }
  }, []);

  function handleAddWidget(widget: WidgetItem) {
    const updated: WidgetWithId[] = [
      ...widgets,
      { ...widget, position: widgets.length },
    ];
    setWidgets(updated);
    persistLayout(updated);
  }

  function handleRemoveWidget(idx: number) {
    const updated = widgets.filter((_, i) => i !== idx);
    setWidgets(updated);
    persistLayout(updated);
  }

  function handleResizeWidget(idx: number, newSize: "sm" | "md" | "lg") {
    const updated = widgets.map((w, i) =>
      i === idx ? { ...w, size: newSize } : w
    );
    setWidgets(updated);
    persistLayout(updated);
  }

  const existingTypes = widgets.map((w) => w.widget_type);

  return (
    <div className="page-container">
      <div className="dashboard-toolbar">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Customise your view — add, remove, or resize widgets
            {saving && <span style={{ marginLeft: "0.5rem", color: "var(--muted)" }}>• saving…</span>}
          </p>
        </div>
        <button type="button" onClick={() => setPickerOpen(true)}>
          + Add Widget
        </button>
      </div>

      {loading ? (
        <div className="status loading">Loading dashboard…</div>
      ) : widgets.length === 0 ? (
        <div className="dashboard-empty">
          <div className="dashboard-empty-icon">🧩</div>
          <h3>Your dashboard is empty</h3>
          <p>Click <strong>+ Add Widget</strong> to get started</p>
          <button type="button" onClick={() => setPickerOpen(true)}>
            + Add Widget
          </button>
        </div>
      ) : (
        <div className="widget-grid">
          {widgets.map((widget, idx) => (
            <div
              key={`${widget.widget_type}-${idx}`}
              className={`widget-card size-${widget.size}`}
            >
              <div className="widget-header">
                <span className="widget-title">
                  {WIDGET_ICONS[widget.widget_type]}{" "}
                  {WIDGET_LABELS[widget.widget_type] ?? widget.widget_type}
                </span>
                <div className="widget-actions">
                  {/* Resize buttons */}
                  {(["sm", "md", "lg"] as const).map((s) => (
                    <button
                      key={s}
                      type="button"
                      className="widget-action-btn"
                      title={`Resize to ${s}`}
                      style={{
                        color: widget.size === s ? "var(--accent)" : undefined,
                      }}
                      onClick={() => handleResizeWidget(idx, s)}
                    >
                      {s === "sm" ? "S" : s === "md" ? "M" : "L"}
                    </button>
                  ))}
                  <button
                    type="button"
                    className="widget-action-btn"
                    title="Remove widget"
                    onClick={() => handleRemoveWidget(idx)}
                  >
                    ✕
                  </button>
                </div>
              </div>
              <div className="widget-body">
                <WidgetContent widget={widget} />
              </div>
            </div>
          ))}
        </div>
      )}

      {pickerOpen && (
        <WidgetPicker
          onClose={() => setPickerOpen(false)}
          onAdd={handleAddWidget}
          existingTypes={existingTypes}
        />
      )}
    </div>
  );
}
