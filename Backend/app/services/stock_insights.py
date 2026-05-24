"""Combined shareholding + financial insights for stock detail modal."""

from app.services.company_profile import get_company_profile
from app.services.financials import get_financials
from app.services.holdings import get_shareholding_history
from app.models import FinancialPeriod, ShareholdingPeriod, StockInsightsResponse


def get_stock_insights(symbol: str) -> StockInsightsResponse:
    symbol = symbol.upper()
    if not symbol.endswith(".NS"):
        symbol = f"{symbol}.NS"

    nse_code = symbol.replace(".NS", "").replace(".BO", "")
    profile = get_company_profile(symbol)
    history = get_shareholding_history(symbol, max_periods=5)
    financials = get_financials(symbol)

    shareholding = [ShareholdingPeriod(**p) for p in history]
    quarterly = [FinancialPeriod(**p) for p in financials.get("quarterly", [])]
    yearly = [FinancialPeriod(**p) for p in financials.get("yearly", [])]
    summary_raw = financials.get("summary", {})

    company_name = profile.get("company_name") or nse_code

    return StockInsightsResponse(
        symbol=symbol,
        company_name=company_name,
        sector=profile.get("sector"),
        industry=profile.get("industry"),
        market_cap_cr=profile.get("market_cap_cr"),
        market_cap_category=profile.get("market_cap_category"),
        shareholding=shareholding,
        financials_quarterly=quarterly,
        financials_yearly=yearly,
        revenue_growth_yoy_pct=summary_raw.get("revenue", {}).get("yoy_pct"),
        revenue_cagr_3y_pct=summary_raw.get("revenue", {}).get("cagr_3y_pct"),
        profit_growth_yoy_pct=summary_raw.get("profit", {}).get("yoy_pct"),
        profit_cagr_3y_pct=summary_raw.get("profit", {}).get("cagr_3y_pct"),
    )
