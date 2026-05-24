"""OHLCV chart data for multiple timeframes via yfinance."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from app.utils.network import without_proxy

logger = logging.getLogger(__name__)

# UI key -> yfinance period/interval + TradingView interval
TIMEFRAME_CONFIG: dict[str, dict[str, str]] = {
    "1D": {"period": "5d", "interval": "15m", "tv_interval": "15"},
    "1W": {"period": "1mo", "interval": "1h", "tv_interval": "60"},
    "1M": {"period": "3mo", "interval": "1d", "tv_interval": "D"},
    "3M": {"period": "6mo", "interval": "1d", "tv_interval": "D"},
    "6M": {"period": "1y", "interval": "1d", "tv_interval": "D"},
    "1Y": {"period": "2y", "interval": "1d", "tv_interval": "D"},
    "5Y": {"period": "5y", "interval": "1wk", "tv_interval": "W"},
}

VALID_TIMEFRAMES = frozenset(TIMEFRAME_CONFIG.keys())


def _normalize_symbol(symbol: str) -> str:
    symbol = symbol.upper().strip()
    if not symbol.endswith((".NS", ".BO")):
        return f"{symbol}.NS"
    return symbol


def _bar_time(idx, interval: str) -> str | int:
    """lightweight-charts: intraday uses unix seconds; daily+ uses YYYY-MM-DD."""
    if hasattr(idx, "to_pydatetime"):
        dt = idx.to_pydatetime()
    else:
        dt = idx
    if interval in ("15m", "1h", "5m", "30m", "60m", "90m"):
        return int(dt.timestamp())
    return dt.strftime("%Y-%m-%d")


def fetch_chart_bars(symbol: str, timeframe: str) -> dict[str, Any]:
    """
    Return OHLCV bars for the requested timeframe.
    Does not enforce screener minimum history length.
    """
    timeframe = timeframe.upper()
    if timeframe not in TIMEFRAME_CONFIG:
        raise ValueError(f"Invalid timeframe. Use one of: {', '.join(sorted(VALID_TIMEFRAMES))}")

    symbol = _normalize_symbol(symbol)
    cfg = TIMEFRAME_CONFIG[timeframe]
    period = cfg["period"]
    interval = cfg["interval"]

    try:
        with without_proxy():
            df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
    except Exception:
        logger.exception("Chart fetch failed for %s", symbol)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "interval": interval,
            "bars": [],
            "tv_interval": cfg["tv_interval"],
        }

    if df is None or df.empty:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "interval": interval,
            "bars": [],
            "tv_interval": cfg["tv_interval"],
        }

    df = df.copy()
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    bars: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        try:
            o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        except (KeyError, TypeError, ValueError):
            continue
        if any(pd.isna(x) for x in (o, h, l, c)):
            continue
        vol = row.get("volume")
        volume = int(vol) if vol is not None and not pd.isna(vol) else None
        bars.append(
            {
                "time": _bar_time(idx, interval),
                "open": round(o, 4),
                "high": round(h, 4),
                "low": round(l, 4),
                "close": round(c, 4),
                "volume": volume,
            }
        )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "interval": interval,
        "bars": bars,
        "tv_interval": cfg["tv_interval"],
    }
