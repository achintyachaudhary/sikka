"""CRUD helpers for all ORM tables."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import (
    DashboardWidget,
    FinancialCache,
    HoldingsCache,
    IpoListing,
    IpoLlmResearch,
    IpoMlFeatureRow,
    IpoResearchRun,
    MarketIndexCache,
    StockProfile,
    UserPreferences,
)

CACHE_STALE_DAYS = 90


def _is_stale(dt: datetime | None) -> bool:
    if dt is None:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - dt > timedelta(days=CACHE_STALE_DAYS)


# ── StockProfile ──────────────────────────────────────────────────────────────

def get_profile(db: Session, symbol: str) -> StockProfile | None:
    return db.get(StockProfile, symbol.upper())


def profile_is_fresh(db: Session, symbol: str) -> bool:
    row = get_profile(db, symbol.upper())
    return row is not None and not _is_stale(row.last_updated)


def upsert_profile(db: Session, symbol: str, data: dict[str, Any]) -> StockProfile:
    symbol = symbol.upper()
    row = db.get(StockProfile, symbol)
    if row is None:
        row = StockProfile(symbol=symbol)
        db.add(row)
    for k, v in data.items():
        setattr(row, k, v)
    row.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


# ── HoldingsCache ─────────────────────────────────────────────────────────────

def get_holdings(db: Session, symbol: str) -> HoldingsCache | None:
    return db.get(HoldingsCache, symbol.upper())


def holdings_is_fresh(db: Session, symbol: str) -> bool:
    row = get_holdings(db, symbol.upper())
    return row is not None and not _is_stale(row.last_fetched)


def upsert_holdings(
    db: Session,
    symbol: str,
    latest: dict[str, Any],
    history: list[dict[str, Any]],
) -> HoldingsCache:
    symbol = symbol.upper()
    row = db.get(HoldingsCache, symbol)
    if row is None:
        row = HoldingsCache(symbol=symbol)
        db.add(row)
    row.promoter_pct = latest.get("promoter_holding_pct")
    row.fii_pct = latest.get("fii_holding_pct")
    row.dii_pct = latest.get("dii_holding_pct")
    row.public_pct = latest.get("public_holding_pct")
    row.retail_pct = latest.get("retail_and_others_pct")
    row.as_of = latest.get("as_of")
    row.history_json = json.dumps(history)
    row.last_fetched = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def get_holdings_history(db: Session, symbol: str) -> list[dict[str, Any]]:
    row = get_holdings(db, symbol.upper())
    if row is None or not row.history_json:
        return []
    try:
        return json.loads(row.history_json)
    except (json.JSONDecodeError, TypeError):
        return []


# ── FinancialCache ────────────────────────────────────────────────────────────

def financials_are_fresh(db: Session, symbol: str) -> bool:
    symbol = symbol.upper()
    rows = (
        db.query(FinancialCache)
        .filter(FinancialCache.symbol == symbol)
        .limit(1)
        .all()
    )
    if not rows:
        return False
    return not _is_stale(rows[0].last_fetched)


def upsert_financials(
    db: Session,
    symbol: str,
    periods: list[dict[str, Any]],
    is_quarterly: bool,
) -> None:
    symbol = symbol.upper()
    db.query(FinancialCache).filter(
        FinancialCache.symbol == symbol,
        FinancialCache.is_quarterly == is_quarterly,
    ).delete()

    now = datetime.now(timezone.utc)
    for p in periods:
        row = FinancialCache(
            symbol=symbol,
            period_label=p.get("label", ""),
            is_quarterly=is_quarterly,
            revenue_cr=p.get("revenue_cr"),
            profit_cr=p.get("profit_cr"),
            period_date=p.get("period"),
            last_fetched=now,
        )
        db.add(row)
    db.commit()


def get_financials_rows(
    db: Session, symbol: str, is_quarterly: bool
) -> list[dict[str, Any]]:
    symbol = symbol.upper()
    rows = (
        db.query(FinancialCache)
        .filter(
            FinancialCache.symbol == symbol,
            FinancialCache.is_quarterly == is_quarterly,
        )
        .order_by(FinancialCache.period_date)
        .all()
    )
    return [
        {
            "period": r.period_date,
            "label": r.period_label,
            "revenue_cr": r.revenue_cr,
            "profit_cr": r.profit_cr,
        }
        for r in rows
    ]


# ── UserPreferences ───────────────────────────────────────────────────────────

def get_pref(db: Session, key: str) -> str | None:
    row = db.get(UserPreferences, key)
    return row.value if row else None


def set_pref(db: Session, key: str, value: str) -> None:
    row = db.get(UserPreferences, key)
    if row is None:
        row = UserPreferences(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()


def get_all_prefs(db: Session) -> dict[str, str]:
    rows = db.query(UserPreferences).all()
    return {r.key: r.value for r in rows}


# ── DashboardWidget ───────────────────────────────────────────────────────────

def list_widgets(db: Session) -> list[dict[str, Any]]:
    rows = db.query(DashboardWidget).order_by(DashboardWidget.position).all()
    return [
        {
            "id": r.id,
            "widget_type": r.widget_type,
            "size": r.size,
            "position": r.position,
            "config": json.loads(r.config_json) if r.config_json else {},
        }
        for r in rows
    ]


# ── MarketIndexCache ──────────────────────────────────────────────────────────

def get_market_index(db: Session, index_id: str) -> MarketIndexCache | None:
    return db.get(MarketIndexCache, index_id.lower())


def upsert_market_index(
    db: Session,
    index_id: str,
    display_name: str,
    yf_symbol: str,
    last_value: float,
    change_abs: float,
    change_pct: float,
    bars_json: str,
    quote_updated_at: datetime,
    bars_updated_at: datetime,
) -> MarketIndexCache:
    index_id = index_id.lower()
    row = db.get(MarketIndexCache, index_id)
    if row is None:
        row = MarketIndexCache(index_id=index_id)
        db.add(row)
    row.display_name = display_name
    row.yf_symbol = yf_symbol
    row.last_value = last_value
    row.change_abs = change_abs
    row.change_pct = change_pct
    row.bars_json = bars_json
    row.quote_updated_at = quote_updated_at
    row.bars_updated_at = bars_updated_at
    db.commit()
    db.refresh(row)
    return row


# ── IpoListing (shared Tracker + Research) ────────────────────────────────────

def get_ipo_listing(db: Session, symbol: str) -> IpoListing | None:
    return db.get(IpoListing, symbol.upper())


def upsert_ipo_listing(db: Session, symbol: str, **fields: Any) -> IpoListing:
    symbol = symbol.upper()
    row = db.get(IpoListing, symbol)
    if row is None:
        row = IpoListing(symbol=symbol, listing_date=fields.get("listing_date", ""))
        db.add(row)
    for key, value in fields.items():
        if hasattr(row, key):
            setattr(row, key, value)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def list_ipo_listings(
    db: Session,
    *,
    symbols: set[str] | None = None,
    ml_ready_only: bool = False,
) -> list[IpoListing]:
    q = db.query(IpoListing)
    if symbols:
        q = q.filter(IpoListing.symbol.in_([s.upper() for s in symbols]))
    if ml_ready_only:
        q = q.filter(IpoListing.ml_status == "ready")
    return q.order_by(IpoListing.listing_date.desc()).all()


def latest_ipo_listing_update(db: Session) -> datetime | None:
    row = db.query(IpoListing).order_by(IpoListing.updated_at.desc()).first()
    return row.updated_at if row else None


def ipo_listing_to_dict(row: IpoListing) -> dict[str, Any]:
    market_status = row.market_status or "pending"
    status = (
        "no_market_data"
        if market_status == "no_market_data"
        else ("listed" if row.current_price is not None else "no_market_data")
    )
    return {
        "symbol": row.symbol,
        "company_name": row.company_name or row.symbol,
        "security_type": row.security_type or "",
        "ipo_start_date": row.ipo_start_date or "",
        "ipo_end_date": row.ipo_end_date or "",
        "listing_date": row.listing_date,
        "listing_date_display": row.listing_date_display or row.listing_date,
        "issue_price": row.issue_price,
        "price_range": row.price_range or "",
        "yf_symbol": row.yf_symbol,
        "listing_open": row.listing_open,
        "listing_close": row.listing_close,
        "listing_high": row.listing_high,
        "current_price": row.current_price,
        "listing_day_gain_pct": row.listing_day_gain_pct,
        "gain_vs_issue_pct": row.gain_vs_issue_pct,
        "gain_vs_listing_close_pct": row.gain_vs_listing_close_pct,
        "gain_listing_open_to_current_pct": row.gain_listing_open_to_current_pct,
        "status": status,
    }


# ── IpoMlFeatureRow (legacy) ──────────────────────────────────────────────────

def get_ipo_ml_row(db: Session, symbol: str) -> IpoMlFeatureRow | None:
    return db.get(IpoMlFeatureRow, symbol.upper())


def upsert_ipo_ml_row(
    db: Session,
    symbol: str,
    listing_date: str,
    company_name: str,
    features_json: str,
    targets_json: str,
    built_at: datetime | None = None,
    enrichment_status: str = "ready",
) -> IpoMlFeatureRow:
    symbol = symbol.upper()
    row = db.get(IpoMlFeatureRow, symbol)
    if row is None:
        row = IpoMlFeatureRow(symbol=symbol)
        db.add(row)
    row.listing_date = listing_date
    row.company_name = company_name
    row.features_json = features_json
    row.targets_json = targets_json
    row.enrichment_status = enrichment_status
    if built_at:
        row.built_at = built_at
    db.commit()
    db.refresh(row)
    return row


def list_ipo_ml_rows(db: Session, *, ready_only: bool = True) -> list[IpoMlFeatureRow]:
    q = db.query(IpoMlFeatureRow)
    if ready_only:
        q = q.filter(IpoMlFeatureRow.enrichment_status == "ready")
    return q.order_by(IpoMlFeatureRow.listing_date.desc()).all()


def count_ipo_ml_rows(db: Session, *, ready_only: bool = False) -> int:
    q = db.query(IpoMlFeatureRow)
    if ready_only:
        q = q.filter(IpoMlFeatureRow.enrichment_status == "ready")
    return q.count()


def latest_ipo_ml_built_at(db: Session) -> datetime | None:
    row = db.query(IpoMlFeatureRow).order_by(IpoMlFeatureRow.built_at.desc()).first()
    return row.built_at if row else None


# ── IpoResearchRun ────────────────────────────────────────────────────────────

def create_ipo_research_run(
    db: Session,
    algorithm: str,
    params_json: str | None = None,
) -> IpoResearchRun:
    run = IpoResearchRun(algorithm=algorithm, status="running", params_json=params_json)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_ipo_research_run(
    db: Session,
    run_id: int,
    *,
    status: str,
    metrics_json: str | None = None,
    insights_json: str | None = None,
    summary_text: str | None = None,
    sample_count: int | None = None,
    error_message: str | None = None,
) -> IpoResearchRun | None:
    run = db.get(IpoResearchRun, run_id)
    if run is None:
        return None
    run.status = status
    if metrics_json is not None:
        run.metrics_json = metrics_json
    if insights_json is not None:
        run.insights_json = insights_json
    if summary_text is not None:
        run.summary_text = summary_text
    if sample_count is not None:
        run.sample_count = sample_count
    if error_message is not None:
        run.error_message = error_message
    if status in ("completed", "failed"):
        run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)
    return run


def list_ipo_research_runs(db: Session, limit: int = 50) -> list[IpoResearchRun]:
    return (
        db.query(IpoResearchRun)
        .order_by(IpoResearchRun.created_at.desc())
        .limit(limit)
        .all()
    )


def get_ipo_research_run(db: Session, run_id: int) -> IpoResearchRun | None:
    return db.get(IpoResearchRun, run_id)


# ── IpoLlmResearch ────────────────────────────────────────────────────────────

def get_ipo_llm_research(db: Session, symbol: str) -> IpoLlmResearch | None:
    return db.get(IpoLlmResearch, symbol.upper())


def upsert_ipo_llm_research(
    db: Session,
    symbol: str,
    provider: str,
    payload_json: str,
    fetched_at: datetime | None = None,
) -> IpoLlmResearch:
    symbol = symbol.upper()
    row = db.get(IpoLlmResearch, symbol)
    if row is None:
        row = IpoLlmResearch(symbol=symbol)
        db.add(row)
    row.provider = provider
    row.status = "fetched"
    row.payload_json = payload_json
    row.error_message = None
    if fetched_at:
        row.fetched_at = fetched_at
    db.commit()
    db.refresh(row)
    return row


def upsert_ipo_llm_failed(
    db: Session,
    symbol: str,
    provider: str,
    error_message: str,
) -> IpoLlmResearch:
    symbol = symbol.upper()
    row = db.get(IpoLlmResearch, symbol)
    if row is None:
        row = IpoLlmResearch(symbol=symbol)
        db.add(row)
    row.provider = provider
    row.status = "failed"
    row.payload_json = row.payload_json or "{}"
    row.error_message = error_message[:2000]
    row.fetched_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def list_ipo_llm_status(
    db: Session,
    symbols: list[str],
) -> dict[str, IpoLlmResearch | None]:
    normalized = [s.upper().replace(".NS", "").strip() for s in symbols if s]
    if not normalized:
        return {}
    rows = (
        db.query(IpoLlmResearch)
        .filter(IpoLlmResearch.symbol.in_(normalized))
        .all()
    )
    by_symbol = {r.symbol: r for r in rows}
    return {s: by_symbol.get(s) for s in normalized}


def save_widgets(db: Session, widgets: list[dict[str, Any]]) -> None:
    db.query(DashboardWidget).delete()
    for i, w in enumerate(widgets):
        row = DashboardWidget(
            widget_type=w["widget_type"],
            size=w.get("size", "md"),
            position=i,
            config_json=json.dumps(w.get("config", {})),
        )
        db.add(row)
    db.commit()
