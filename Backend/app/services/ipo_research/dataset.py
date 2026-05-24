"""Build and cache IPO ML feature rows (all historical equity IPOs)."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

from app.db import crud
from app.db.database import SessionLocal
from app.services.ipo_fetcher import (
    fetch_all_past_ipos,
    filter_all_equity_ipos,
    is_tradeable_equity_symbol,
)
from app.services.ipo_performance import enrich_ipos_parallel
from app.services.ipo_research.market_features import market_features_at_listing
from app.services.market_indices import ensure_market_indices_refreshed

logger = logging.getLogger(__name__)


def _subscription_features(symbol: str) -> dict[str, Any]:
    with SessionLocal() as db:
        row = crud.get_ipo_llm_research(db, symbol)
    if row is None or (row.status or "") != "fetched":
        return {
            "has_subscription_data": 0,
            "overall_times_subscribed": None,
            "qib_times_subscribed": None,
            "nii_times_subscribed": None,
            "retail_times_subscribed": None,
        }
    try:
        payload = json.loads(row.payload_json)
        sub = payload.get("subscription_summary") or {}
        cats = sub.get("category_breakdown") or {}

        def _times(key: str) -> float | None:
            cat = cats.get(key) or {}
            v = cat.get("times_subscribed")
            return float(v) if v is not None else None

        overall = sub.get("overall_times_subscribed")
        return {
            "has_subscription_data": 1,
            "overall_times_subscribed": float(overall) if overall is not None else None,
            "qib_times_subscribed": _times("qualified_institutional_buyers_qib"),
            "nii_times_subscribed": _times("non_institutional_investors_nii"),
            "retail_times_subscribed": _times("retail_individual_investors_rii"),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {"has_subscription_data": 0}


def _targets_from_enriched(row: dict) -> dict[str, Any]:
    ld = row.get("listing_day_gain_pct")
    gi = row.get("gain_vs_issue_pct")
    gl = row.get("gain_listing_open_to_current_pct")

    return {
        "profit_listing_day": 1 if ld is not None and ld > 0 else 0 if ld is not None else None,
        "profit_vs_issue": 1 if gi is not None and gi > 0 else 0 if gi is not None else None,
        "strong_profit_vs_issue": 1 if gi is not None and gi >= 15 else 0 if gi is not None else None,
        "profit_buy_listing_open": 1 if gl is not None and gl > 0 else 0 if gl is not None else None,
        "listing_day_gain_pct": ld,
        "gain_vs_issue_pct": gi,
        "gain_listing_open_to_current_pct": gl,
    }


def _features_from_row(enriched: dict, market: dict[str, Any], sub: dict[str, Any]) -> dict[str, Any]:
    is_sme = 1 if (enriched.get("security_type") or "").upper() == "SME" else 0
    issue_price = enriched.get("issue_price")

    feats = {
        "symbol": enriched["symbol"],
        "listing_date": enriched["listing_date"],
        "security_type_sme": is_sme,
        "issue_price": issue_price,
        "issue_price_log": (
            float(math.log(issue_price)) if issue_price and issue_price > 0 else None
        ),
        **market,
        **{k: v for k, v in sub.items() if k != "has_subscription_data"},
        "has_subscription_data": sub.get("has_subscription_data", 0),
    }
    return feats


def build_row(enriched: dict) -> dict[str, Any] | None:
    if enriched.get("status") == "no_market_data":
        return None
    market = market_features_at_listing(enriched["listing_date"])
    sub = _subscription_features(enriched["symbol"])
    features = _features_from_row(enriched, market, sub)
    targets = _targets_from_enriched(enriched)
    if targets.get("profit_vs_issue") is None:
        return None
    return {
        "symbol": enriched["symbol"],
        "listing_date": enriched["listing_date"],
        "company_name": enriched.get("company_name", ""),
        "features": features,
        "targets": targets,
    }


def count_pending_ipo_rows() -> int:
    raw = fetch_all_past_ipos()
    ipo_rows = filter_all_equity_ipos(raw)
    pending = 0
    with SessionLocal() as db:
        for row in ipo_rows:
            cached = crud.get_ipo_ml_row(db, row["symbol"])
            if cached is None:
                pending += 1
    return pending


def prepare_ipo_dataset(
    *,
    force_refresh: bool = False,
    batch_size: int = 40,
) -> dict[str, Any]:
    """
    Load all equity IPOs from NSE, enrich prices, cache per-symbol features in DB.
  Returns summary stats.
    """
    ensure_market_indices_refreshed()
    raw = fetch_all_past_ipos()
    ipo_rows = filter_all_equity_ipos(raw)
    skipped_invalid_symbols = max(0, len(raw) - len(ipo_rows))

    to_enrich: list[dict] = []
    skipped_cached = 0

    with SessionLocal() as db:
        for row in ipo_rows:
            cached = crud.get_ipo_ml_row(db, row["symbol"])
            if cached and not force_refresh:
                skipped_cached += 1
                continue
            to_enrich.append(row)

    if batch_size > 0:
        to_enrich = to_enrich[:batch_size]

    enriched_new = enrich_ipos_parallel(to_enrich) if to_enrich else []

    saved = 0
    failed = 0
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        for enriched in enriched_new:
            built = build_row(enriched)
            if built is None:
                failed += 1
                continue
            crud.upsert_ipo_ml_row(
                db,
                symbol=built["symbol"],
                listing_date=built["listing_date"],
                company_name=built.get("company_name", ""),
                features_json=json.dumps(built["features"]),
                targets_json=json.dumps(built["targets"]),
                built_at=now,
            )
            saved += 1

    total_in_db = 0
    with SessionLocal() as db:
        total_in_db = crud.count_ipo_ml_rows(db)

    return {
        "total_nse_ipos": len(ipo_rows),
        "skipped_invalid_symbols": skipped_invalid_symbols,
        "newly_enriched": len(enriched_new),
        "newly_saved": saved,
        "skipped_cached": skipped_cached,
        "failed_enrich": failed,
        "no_market_data": sum(1 for e in enriched_new if e.get("status") == "no_market_data"),
        "total_dataset_rows": total_in_db,
        "pending_remaining": count_pending_ipo_rows(),
    }


def load_dataset_dataframe():
    """Load cached dataset as pandas DataFrame for ML."""
    import pandas as pd

    rows = []
    with SessionLocal() as db:
        for row in crud.list_ipo_ml_rows(db):
            feats = json.loads(row.features_json)
            tgts = json.loads(row.targets_json)
            rows.append({**feats, **{f"target_{k}": v for k, v in tgts.items()}})

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def dataset_stats() -> dict[str, Any]:
    with SessionLocal() as db:
        count = crud.count_ipo_ml_rows(db)
        latest = crud.latest_ipo_ml_built_at(db)

    return {
        "total_rows": count,
        "latest_built_at": latest.isoformat() if latest else None,
        "min_rows_for_ml": 30,
        "ready_for_ml": count >= 30,
    }
