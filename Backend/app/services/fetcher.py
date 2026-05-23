"""yfinance data fetching and normalization."""

import logging

import pandas as pd
import yfinance as yf

from app.config import HISTORY_PERIOD

logger = logging.getLogger(__name__)


def fetch_history(symbol: str, period: str = HISTORY_PERIOD) -> pd.DataFrame | None:
    """Download OHLCV history for a single symbol."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, auto_adjust=True)
    except Exception:
        logger.exception("Failed to fetch %s", symbol)
        return None

    if df is None or df.empty:
        logger.warning("No data for %s", symbol)
        return None

    df = df.copy()
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

    required = {"close", "high", "low", "open", "volume"}
    if not required.issubset(set(df.columns)):
        logger.warning("Missing columns for %s: %s", symbol, list(df.columns))
        return None

    df = df.dropna(subset=["close"])
    if len(df) < 55:
        logger.warning("Insufficient history for %s (%d rows)", symbol, len(df))
        return None

    return df
