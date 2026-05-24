import { displaySymbol, tradingViewChartUrl } from "../utils/tradingView";

interface SymbolLinkProps {
  symbol: string;
  yfSymbol?: string | null;
}

export default function SymbolLink({ symbol, yfSymbol }: SymbolLinkProps) {
  const label = displaySymbol(symbol);
  const href = tradingViewChartUrl(symbol, yfSymbol);

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="symbol-link"
      title={`Open ${label} on TradingView`}
    >
      <strong>{label}</strong>
    </a>
  );
}
