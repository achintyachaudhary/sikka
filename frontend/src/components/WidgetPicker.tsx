import { useEffect, useRef, useState } from "react";
import type { WidgetItem } from "../api";

interface WidgetDef {
  type: string;
  name: string;
  icon: string;
  description: string;
  defaultSize: "sm" | "md" | "lg";
}

const AVAILABLE_WIDGETS: WidgetDef[] = [
  {
    type: "bullish_stocks",
    name: "Bullish Stocks",
    icon: "📊",
    description: "Top screener results from Nifty 50",
    defaultSize: "md",
  },
  {
    type: "recent_ipos",
    name: "Recent IPOs",
    icon: "🚀",
    description: "IPOs listed in the last 2 months",
    defaultSize: "md",
  },
  {
    type: "index_summary",
    name: "Index Summary",
    icon: "📈",
    description: "Nifty 50, Bank Nifty, Sensex snapshot",
    defaultSize: "sm",
  },
  {
    type: "top_movers",
    name: "Top Movers",
    icon: "⚡",
    description: "Top gainers and losers (5-day)",
    defaultSize: "sm",
  },
];

interface Props {
  onClose: () => void;
  onAdd: (widget: WidgetItem) => void;
  existingTypes: string[];
}

export default function WidgetPicker({ onClose, onAdd, existingTypes }: Props) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [size, setSize] = useState<"sm" | "md" | "lg">("md");
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const def = AVAILABLE_WIDGETS.find((w) => w.type === selectedType);
    if (def) setSize(def.defaultSize);
  }, [selectedType]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function handleBackdrop(e: React.MouseEvent) {
    if (e.target === backdropRef.current) onClose();
  }

  function handleAdd() {
    if (!selectedType) return;
    onAdd({
      widget_type: selectedType,
      size,
      position: 0,
      config: {},
    });
    onClose();
  }

  return (
    <div className="widget-picker-backdrop" ref={backdropRef} onClick={handleBackdrop}>
      <div className="widget-picker-panel" role="dialog" aria-modal="true">
        <div className="widget-picker-header">
          <h3>Add Widget</h3>
          <button type="button" className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="widget-picker-body">
          <div className="widget-picker-grid">
            {AVAILABLE_WIDGETS.map((w) => {
              const alreadyAdded = existingTypes.includes(w.type);
              return (
                <div
                  key={w.type}
                  className={`widget-option${selectedType === w.type ? " selected" : ""}${alreadyAdded ? "" : ""}`}
                  onClick={() => !alreadyAdded && setSelectedType(w.type)}
                  style={alreadyAdded ? { opacity: 0.5, cursor: "default" } : { cursor: "pointer" }}
                  role="button"
                  tabIndex={alreadyAdded ? -1 : 0}
                  onKeyDown={(e) => e.key === "Enter" && !alreadyAdded && setSelectedType(w.type)}
                >
                  <div className="widget-option-icon">{w.icon}</div>
                  <div className="widget-option-name">
                    {w.name}
                    {alreadyAdded && (
                      <span style={{ marginLeft: "0.4rem", fontSize: "0.7rem", color: "var(--green)" }}>
                        ✓ added
                      </span>
                    )}
                  </div>
                  <div className="widget-option-desc">{w.description}</div>
                </div>
              );
            })}
          </div>

          {selectedType && (
            <div className="widget-size-row" style={{ marginTop: "1rem" }}>
              <span>Size:</span>
              {(["sm", "md", "lg"] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  className={`size-btn${size === s ? " active" : ""}`}
                  onClick={() => setSize(s)}
                >
                  {s === "sm" ? "Small" : s === "md" ? "Medium" : "Large"}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="widget-picker-footer">
          <button
            type="button"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              color: "var(--text)",
            }}
            onClick={onClose}
          >
            Cancel
          </button>
          <button type="button" disabled={!selectedType} onClick={handleAdd}>
            Add Widget
          </button>
        </div>
      </div>
    </div>
  );
}
