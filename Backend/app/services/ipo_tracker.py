"""IPO tracker orchestration."""

from datetime import datetime, timezone

from app.services.ipo_fetcher import fetch_all_past_ipos, filter_recent_ipos
from app.services.ipo_performance import enrich_ipos_parallel
from app.models import IpoListing, IpoTrackResponse

_performance_cache: dict[str, tuple[float, IpoTrackResponse]] = {}
CACHE_TTL = 1800  # 30 minutes


def track_recent_ipos(months: int = 2, refresh: bool = False) -> IpoTrackResponse:
    if months not in (1, 2):
        months = 2

    cache_key = str(months)
    now_ts = datetime.now(timezone.utc).timestamp()

    if not refresh:
        cached = _performance_cache.get(cache_key)
        if cached and now_ts < cached[0]:
            return cached[1]

    raw = fetch_all_past_ipos()
    filtered = filter_recent_ipos(raw, months=months)
    enriched = enrich_ipos_parallel(filtered)

    with_data = sum(1 for r in enriched if r.get("current_price") is not None)
    listings = [IpoListing(**row) for row in enriched]

    response = IpoTrackResponse(
        scanned_at=datetime.now(timezone.utc).isoformat(),
        months=months,
        total_listed=len(listings),
        with_market_data=with_data,
        results=listings,
    )

    _performance_cache[cache_key] = (now_ts + CACHE_TTL, response)
    return response
