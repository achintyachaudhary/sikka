"""Dashboard and preferences API routes."""

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

dashboard_router = APIRouter(prefix="/api")

# ── Pydantic schemas for request bodies ──────────────────────────────────────

class WidgetItem(BaseModel):
    widget_type: str
    size: str = "md"
    position: int = 0
    config: dict[str, Any] = {}


class LayoutPayload(BaseModel):
    widgets: list[WidgetItem]


class PreferencesPayload(BaseModel):
    preferences: dict[str, str]


class MarketIndexQuote(BaseModel):
    index_id: str
    display_name: str
    yf_symbol: str
    last_value: float | None = None
    change_abs: float | None = None
    change_pct: float | None = None
    updated_at: str | None = None


class MarketIndicesResponse(BaseModel):
    indices: list[MarketIndexQuote]


class MarketIndexChartResponse(BaseModel):
    index_id: str
    display_name: str
    yf_symbol: str
    timeframe: str
    interval: str
    bars: list[dict[str, Any]] = Field(default_factory=list)


# ── In-memory cache for widget data (avoids re-scanning on every dashboard load) ─
_widget_cache: dict[str, Any] = {}
_WIDGET_CACHE_TTL = 300  # 5 minutes


def _cached_widget(key: str, compute_fn):
    now = time.time()
    entry = _widget_cache.get(key)
    if entry and now < entry["expires_at"]:
        return entry["data"]
    data = compute_fn()
    _widget_cache[key] = {"data": data, "expires_at": now + _WIDGET_CACHE_TTL}
    return data


# ── Layout endpoints ──────────────────────────────────────────────────────────

@dashboard_router.get("/dashboard/layout")
def get_layout(db: Session = Depends(get_db)) -> dict[str, Any]:
    widgets = crud.list_widgets(db)
    return {"widgets": widgets}


@dashboard_router.put("/dashboard/layout")
def save_layout(payload: LayoutPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    crud.save_widgets(db, [w.model_dump() for w in payload.widgets])
    return {"saved": len(payload.widgets)}


# ── Preferences endpoints ─────────────────────────────────────────────────────

@dashboard_router.get("/preferences")
def get_preferences(db: Session = Depends(get_db)) -> dict[str, Any]:
    return {"preferences": crud.get_all_prefs(db)}


@dashboard_router.put("/preferences")
def update_preferences(
    payload: PreferencesPayload, db: Session = Depends(get_db)
) -> dict[str, Any]:
    for key, value in payload.preferences.items():
        crud.set_pref(db, key, value)
    return {"saved": len(payload.preferences)}


# ── Widget data endpoints ─────────────────────────────────────────────────────

@dashboard_router.get("/market-indices", response_model=MarketIndicesResponse)
def market_indices(
    refresh: bool = Query(False, description="Force refresh from yfinance"),
) -> MarketIndicesResponse:
    from app.services.market_indices import ensure_market_indices_refreshed, list_market_indices

    if refresh:
        ensure_market_indices_refreshed(force=True)
    indices = list_market_indices(refresh_if_stale=not refresh)
    return MarketIndicesResponse(indices=[MarketIndexQuote(**i) for i in indices])


@dashboard_router.get("/market-indices/{index_id}/chart", response_model=MarketIndexChartResponse)
def market_index_chart(index_id: str) -> MarketIndexChartResponse:
    from app.services.market_indices import get_market_index_chart

    try:
        raw = get_market_index_chart(index_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MarketIndexChartResponse(**raw)


@dashboard_router.post("/market-indices/refresh")
def market_indices_refresh() -> dict[str, str]:
    from app.services.market_indices import ensure_market_indices_refreshed

    ensure_market_indices_refreshed(force=True)
    return {"status": "ok"}


@dashboard_router.get("/widgets/index-summary")
def index_summary() -> dict[str, Any]:
    """Quick snapshot of Nifty index benchmark data."""

    def _fetch():
        try:
            import yfinance as yf

            from app.utils.network import without_proxy

            indices = {
                "Nifty 50": "^NSEI",
                "Nifty Bank": "^NSEBANK",
                "Sensex": "^BSESN",
            }
            result = []
            for name, ticker in indices.items():
                try:
                    with without_proxy():
                        t = yf.Ticker(ticker)
                        hist = t.history(period="2d")
                    if hist.empty:
                        continue
                    latest = float(hist["Close"].iloc[-1])
                    prev = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else latest
                    chg = round((latest - prev) / prev * 100, 2) if prev else 0
                    result.append(
                        {
                            "name": name,
                            "value": round(latest, 2),
                            "change_pct": chg,
                        }
                    )
                except Exception:
                    pass
            return {"indices": result}
        except Exception:
            return {"indices": []}

    return _cached_widget("index_summary", _fetch)


@dashboard_router.get("/widgets/top-movers")
def top_movers() -> dict[str, Any]:
    """Top 5 gainers and losers from the last Nifty 50 scan cache."""
    from app.services.screener import run_scan
    from app.watchlists.indices import IndexId

    def _fetch():
        try:
            scan = run_scan(min_score=0, limit=50, index=IndexId.NIFTY_50)
            all_stocks = scan.results
            with_change = [s for s in all_stocks if s.change_5d_pct is not None]
            gainers = sorted(with_change, key=lambda s: s.change_5d_pct or 0, reverse=True)[:5]
            losers = sorted(with_change, key=lambda s: s.change_5d_pct or 0)[:5]
            return {
                "gainers": [
                    {
                        "symbol": s.symbol,
                        "price": s.price,
                        "change_5d_pct": s.change_5d_pct,
                    }
                    for s in gainers
                ],
                "losers": [
                    {
                        "symbol": s.symbol,
                        "price": s.price,
                        "change_5d_pct": s.change_5d_pct,
                    }
                    for s in losers
                ],
            }
        except Exception:
            return {"gainers": [], "losers": []}

    return _cached_widget("top_movers", _fetch)
