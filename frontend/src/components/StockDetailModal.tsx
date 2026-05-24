import { useEffect } from "react";
import type { SelectedStock } from "../types";
import StockDetailContent from "./StockDetailContent";
import SymbolLink from "./SymbolLink";
import { displaySymbol } from "../utils/tradingView";

interface StockDetailModalProps {
  stock: SelectedStock | null;
  onClose: () => void;
}

export default function StockDetailModal({
  stock,
  onClose,
}: StockDetailModalProps) {
  useEffect(() => {
    if (!stock) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [stock, onClose]);

  if (!stock) return null;

  const title = stock.label || displaySymbol(stock.symbol);

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="stock-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          <div className="modal-title-wrap">
            <h2 id="stock-modal-title">{title}</h2>
            <SymbolLink
              symbol={stock.yfSymbol || stock.symbol}
            />
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </header>

        <div className="modal-body">
          <StockDetailContent
            symbol={stock.symbol}
            yfSymbol={stock.yfSymbol}
          />
        </div>
      </div>
    </div>
  );
}
