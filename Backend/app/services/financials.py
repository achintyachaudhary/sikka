"""Company financial statements via yfinance."""

from __future__ import annotations

import logging
from datetime import datetime

import yfinance as yf

from app.utils.network import without_proxy

logger = logging.getLogger(__name__)

REVENUE_ROWS = ("Total Revenue", "Operating Revenue")
PROFIT_ROWS = ("Net Income Common Stockholders", "Net Income")


def _yf_symbol(symbol: str) -> str:
    symbol = symbol.upper()
    if not symbol.endswith((".NS", ".BO")):
        return f"{symbol}.NS"
    return symbol


def _period_label(dt: datetime, yearly: bool) -> str:
    if yearly:
        return str(dt.year)
    return dt.strftime("%b '%y")


def _to_crores(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value / 1e7, 2)


def _pick_row(df, names: tuple[str, ...]):
    for name in names:
        if name in df.index:
            return df.loc[name]
    return None


def _series_to_periods(series, yearly: bool) -> list[dict]:
    if series is None:
        return []

    items: list[dict] = []
    for col in series.index:
        val = series[col]
        if val is None or (hasattr(val, "__float__") and str(val) == "nan"):
            continue
        try:
            num = float(val)
        except (TypeError, ValueError):
            continue
        if num == 0:
            continue
        dt = col.to_pydatetime() if hasattr(col, "to_pydatetime") else col
        items.append(
            {
                "period": dt.strftime("%Y-%m-%d"),
                "label": _period_label(dt, yearly),
                "value_cr": _to_crores(num),
            },
        )

    items.sort(key=lambda x: x["period"])
    return items[-8:] if yearly else items[-8:]


def _pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return round(((current - previous) / abs(previous)) * 100, 2)


def _growth_summary(periods: list[dict]) -> dict[str, float | None]:
    if len(periods) < 2:
        return {"yoy_pct": None, "cagr_3y_pct": None}

    latest = periods[-1]["value_cr"]
    prev = periods[-2]["value_cr"]
    yoy = _pct_change(latest, prev)

    cagr = None
    if len(periods) >= 4:
        start = periods[-4]["value_cr"]
        if start and start > 0 and latest is not None:
            cagr = round(((latest / start) ** (1 / 3) - 1) * 100, 2)

    return {"yoy_pct": yoy, "cagr_3y_pct": cagr}


def get_financials(symbol: str) -> dict:
    yf_sym = _yf_symbol(symbol)
    try:
        with without_proxy():
            ticker = yf.Ticker(yf_sym)
            quarterly = ticker.quarterly_income_stmt
            annual = ticker.income_stmt
    except Exception:
        logger.exception("Financial fetch failed for %s", symbol)
        return {"quarterly": [], "yearly": [], "summary": {}}

    q_rev = _series_to_periods(_pick_row(quarterly, REVENUE_ROWS), yearly=False)
    q_profit = _series_to_periods(_pick_row(quarterly, PROFIT_ROWS), yearly=False)
    y_rev = _series_to_periods(_pick_row(annual, REVENUE_ROWS), yearly=True)
    y_profit = _series_to_periods(_pick_row(annual, PROFIT_ROWS), yearly=True)

    def merge(rev_list: list[dict], profit_list: list[dict]) -> list[dict]:
        profit_by_period = {p["period"]: p["value_cr"] for p in profit_list}
        merged = []
        for r in rev_list:
            merged.append(
                {
                    "period": r["period"],
                    "label": r["label"],
                    "revenue_cr": r["value_cr"],
                    "profit_cr": profit_by_period.get(r["period"]),
                },
            )
        return merged

    quarterly_merged = merge(q_rev, q_profit)
    yearly_merged = merge(y_rev, y_profit)

    return {
        "quarterly": quarterly_merged,
        "yearly": yearly_merged,
        "summary": {
            "revenue": _growth_summary([{"value_cr": p["revenue_cr"]} for p in quarterly_merged if p.get("revenue_cr")]),
            "profit": _growth_summary([{"value_cr": p["profit_cr"]} for p in quarterly_merged if p.get("profit_cr")]),
        },
    }
