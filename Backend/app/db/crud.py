"""CRUD helpers for all ORM tables."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import (
    DashboardWidget,
    FinancialCache,
    HoldingsCache,
    IpoLlmResearch,
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
