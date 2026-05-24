/** Build TradingView India chart URL for an NSE/BSE symbol. */
export function tradingViewChartUrl(symbol: string, yfSymbol?: string | null): string {
  const raw = (yfSymbol || symbol).toUpperCase().replace(/\.(NS|BO)$/, "");
  let exchange = "NSE";

  if (yfSymbol?.toUpperCase().endsWith(".BO")) {
    exchange = "BSE";
  } else if (symbol.toUpperCase().endsWith(".BO")) {
    exchange = "BSE";
  }

  const tvSymbol = `${exchange}:${raw}`;
  return `https://in.tradingview.com/chart/?symbol=${encodeURIComponent(tvSymbol)}`;
}

export function displaySymbol(symbol: string): string {
  return symbol.replace(/\.(NS|BO)$/i, "");
}
