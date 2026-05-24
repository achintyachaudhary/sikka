"""IPO Research dataset — uses shared ipo_listings catalog."""

from __future__ import annotations

from typing import Any

from app.services.ipo_catalog import (
    DEFAULT_TRACKER_MONTHS,
    build_ml_features_for_catalog,
    dataset_stats,
    load_ml_dataframe,
    sync_ipo_catalog,
)


def prepare_ipo_dataset(
    *,
    force_refresh: bool = False,
    batch_size: int = 40,
    months: int | None = DEFAULT_TRACKER_MONTHS,
) -> dict[str, Any]:
    """
    1) Sync prices into shared ipo_listings (same DB as IPO Tracker).
    2) Build ML features for all IPOs that have Yahoo price data.
    """
    pending = 1
    sync_result: dict[str, Any] = {}
    batch_num = 0

    while pending > 0:
        batch_num += 1
        sync_result = sync_ipo_catalog(
            months=months,
            force_refresh=force_refresh and batch_num == 1,
            batch_size=batch_size,
        )
        pending = sync_result.get("pending_remaining", 0)
        if sync_result.get("newly_enriched", 0) == 0 and pending > 0:
            break

    ml_result = build_ml_features_for_catalog(months=months, force=force_refresh)

    return {
        "total_nse_ipos": sync_result.get("total_nse_ipos", ml_result.get("catalog_total", 0)),
        "months_back": months or 0,
        "months": months,
        "skipped_invalid_symbols": 0,
        "newly_enriched": sync_result.get("newly_enriched", 0),
        "newly_saved": ml_result.get("ml_built", 0),
        "skipped_cached": sync_result.get("skipped_cached", 0),
        "failed_enrich": 0,
        "skipped_no_market_data": sync_result.get("no_market_data", 0),
        "no_market_data": sync_result.get("no_market_data", 0),
        "catalog_total": ml_result.get("catalog_total", 0),
        "with_market_data": ml_result.get("with_market_data", 0),
        "total_dataset_rows": ml_result.get("ml_ready", 0),
        "ml_ready": ml_result.get("ml_ready", 0),
        "total_rows_attempted": ml_result.get("catalog_total", 0),
        "pending_remaining": sync_result.get("pending_remaining", 0),
    }


def load_dataset_dataframe():
    return load_ml_dataframe()
