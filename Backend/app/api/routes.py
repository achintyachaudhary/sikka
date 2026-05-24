"""API route handlers."""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Query

from app.config import CACHE_TTL_SECONDS, DEFAULT_MIN_SCORE, DEFAULT_SCAN_LIMIT
from app.models import (
    ChartResponse,
    HealthResponse,
    IndicesResponse,
    IndexOption,
    IpoTrackResponse,
    OhlcBar,
    ScanResponse,
    StockDetail,
    StockInsightsResponse,
)
from app.schemas.ipo_llm import (
    IpoBatchFetchRequest,
    IpoBatchFetchResponse,
    IpoLlmResearchResponse,
    IpoLlmStatusResponse,
)
from app.services.ipo_llm_research import (
    batch_fetch_ipo_research,
    fetch_and_store_ipo_research,
    get_cached_ipo_research,
    get_ipo_llm_status_map,
)
from app.services.chart_data import VALID_TIMEFRAMES, fetch_chart_bars
from app.services.ipo_tracker import track_recent_ipos
from app.services.screener import analyze_symbol_detail, run_scan
from app.services.stock_insights import get_stock_insights
from app.watchlists.indices import IndexId, get_index_options
from app.watchlists.loader import get_watchlist_count

router = APIRouter()

_scan_cache: dict[str, Any] = {"payload": None, "expires_at": 0.0}


def _get_cached_scan(min_score: int, limit: int, index: IndexId) -> ScanResponse:
    key = f"{index.value}:{min_score}:{limit}"
    now = time.time()
    cached = _scan_cache.get("key")
    if (
        cached == key
        and _scan_cache.get("payload") is not None
        and now < _scan_cache.get("expires_at", 0)
    ):
        return _scan_cache["payload"]

    result = run_scan(min_score=min_score, limit=limit, index=index)
    _scan_cache["key"] = key
    _scan_cache["payload"] = result
    _scan_cache["expires_at"] = now + CACHE_TTL_SECONDS
    return result


def _parse_index(index: str) -> IndexId:
    try:
        return IndexId(index.lower())
    except ValueError as exc:
        valid = ", ".join(i.value for i in IndexId)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid index '{index}'. Use one of: {valid}",
        ) from exc


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


APPROX_SYMBOL_COUNTS: dict[str, int] = {
    IndexId.NIFTY_50.value: 50,
    IndexId.NIFTY_100.value: 100,
    IndexId.NIFTY_200.value: 200,
    IndexId.NIFTY_500.value: 500,
    IndexId.NSE_ALL.value: 2100,
}


@router.get("/api/indices", response_model=IndicesResponse)
def list_indices() -> IndicesResponse:
    options = get_index_options()
    return IndicesResponse(
        indices=[
            IndexOption(
                id=opt["id"],
                label=opt["label"],
                description=_index_description(
                    opt["description"],
                    opt["id"],
                ),
                slow_scan=bool(opt.get("slow_scan")),
            )
            for opt in options
        ],
    )


def _index_description(base: str, index_id: str) -> str:
    idx = IndexId(index_id)
    count = get_watchlist_count(idx) or APPROX_SYMBOL_COUNTS.get(index_id, 0)
    return f"{base} (~{count} symbols)"


@router.get("/api/scan", response_model=ScanResponse)
def scan(
    index: str = Query(IndexId.NIFTY_50.value, description="Watchlist: nifty50, nifty100, ..."),
    min_score: int = Query(DEFAULT_MIN_SCORE, ge=0, le=12),
    limit: int = Query(DEFAULT_SCAN_LIMIT, ge=1, le=500),
    refresh: bool = Query(False, description="Bypass cache"),
) -> ScanResponse:
    index_id = _parse_index(index)
    if refresh:
        _scan_cache["expires_at"] = 0
    return _get_cached_scan(min_score=min_score, limit=limit, index=index_id)


@router.get("/api/ipo", response_model=IpoTrackResponse)
def ipo_tracker(
    months: int = Query(2, ge=1, le=6, description="Look back 1, 2, or 6 months"),
    refresh: bool = Query(False, description="Bypass cache"),
) -> IpoTrackResponse:
    return track_recent_ipos(months=months, refresh=refresh)


@router.get("/api/ipo/llm-research/status", response_model=IpoLlmStatusResponse)
def ipo_llm_research_status(
    symbols: str = Query(..., description="Comma-separated NSE symbols"),
) -> IpoLlmStatusResponse:
    symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    return get_ipo_llm_status_map(symbol_list)


@router.post("/api/ipo/llm-research/batch", response_model=IpoBatchFetchResponse)
def ipo_llm_research_batch(body: IpoBatchFetchRequest) -> IpoBatchFetchResponse:
    try:
        return batch_fetch_ipo_research(body.items, skip_fetched=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/ipo/{symbol}/llm-research", response_model=IpoLlmResearchResponse)
def get_ipo_llm_research(symbol: str) -> IpoLlmResearchResponse:
    result = get_cached_ipo_research(symbol)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No IPO LLM research cached for {symbol}. POST to generate.",
        )
    return result


@router.post("/api/ipo/{symbol}/llm-research", response_model=IpoLlmResearchResponse)
def generate_ipo_llm_research(
    symbol: str,
    company_name: str | None = Query(None, description="Optional company name for prompt"),
    refresh: bool = Query(False, description="Bypass cache and call LLM again"),
) -> IpoLlmResearchResponse:
    try:
        return fetch_and_store_ipo_research(
            symbol,
            company_name=company_name,
            force_refresh=refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("IPO LLM research failed for %s", symbol)
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}") from exc


@router.get("/api/stock/{symbol}/chart", response_model=ChartResponse)
def stock_chart(
    symbol: str,
    timeframe: str = Query("1M", description="1D, 1W, 1M, 3M, 6M, 1Y, 5Y"),
) -> ChartResponse:
    tf = timeframe.upper()
    if tf not in VALID_TIMEFRAMES:
        valid = ", ".join(sorted(VALID_TIMEFRAMES))
        raise HTTPException(status_code=400, detail=f"Invalid timeframe '{timeframe}'. Use: {valid}")
    raw = fetch_chart_bars(symbol, tf)
    return ChartResponse(
        symbol=raw["symbol"],
        timeframe=raw["timeframe"],
        interval=raw["interval"],
        tv_interval=raw["tv_interval"],
        bars=[OhlcBar(**b) for b in raw["bars"]],
    )


@router.get("/api/stock/{symbol}/insights", response_model=StockInsightsResponse)
def stock_insights(symbol: str) -> StockInsightsResponse:
    return get_stock_insights(symbol)


@router.post("/api/refresh/stock/{symbol}", response_model=StockInsightsResponse)
def refresh_stock(symbol: str) -> StockInsightsResponse:
    """Force-refresh all DB-cached data (profile, holdings, financials) for a symbol."""
    return get_stock_insights(symbol, force_refresh=True)


@router.get("/api/stock/{symbol}", response_model=StockDetail)
def stock_detail(symbol: str) -> StockDetail:
    detail = analyze_symbol_detail(symbol)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No data for symbol: {symbol}")
    return detail
