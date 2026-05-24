"""SQLAlchemy ORM table definitions."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class StockProfile(Base):
    """Cached company profile: sector, industry, market cap, overall score."""

    __tablename__ = "stock_profiles"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    market_cap_cr: Mapped[float | None] = mapped_column(Float, nullable=True)
    cap_category: Mapped[str | None] = mapped_column(String, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class HoldingsCache(Base):
    """Latest (most recent period) shareholding snapshot per symbol."""

    __tablename__ = "holdings_cache"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    promoter_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fii_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    dii_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    public_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    retail_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    as_of: Mapped[str | None] = mapped_column(String, nullable=True)
    last_fetched: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
    # Full historical JSON stored as text for the modal chart
    history_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class FinancialCache(Base):
    """One row per (symbol, period_label, is_quarterly) financial data point."""

    __tablename__ = "financial_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String, index=True, nullable=False)
    period_label: Mapped[str] = mapped_column(String, nullable=False)
    is_quarterly: Mapped[bool] = mapped_column(Boolean, default=True)
    revenue_cr: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_cr: Mapped[float | None] = mapped_column(Float, nullable=True)
    period_date: Mapped[str | None] = mapped_column(String, nullable=True)
    last_fetched: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )


class UserPreferences(Base):
    """Generic key-value store for user settings (theme, etc.)."""

    __tablename__ = "user_preferences"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class DashboardWidget(Base):
    """One row per widget in the user's dashboard layout."""

    __tablename__ = "dashboard_widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    widget_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[str] = mapped_column(String, default="md")  # sm | md | lg
    position: Mapped[int] = mapped_column(Integer, default=0)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketIndexCache(Base):
    """Cached quote + 1Y daily bars for NIFTY / BANKNIFTY / SENSEX."""

    __tablename__ = "market_index_cache"

    index_id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    yf_symbol: Mapped[str] = mapped_column(String, nullable=False)
    last_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_abs: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    bars_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    bars_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class IpoLlmResearch(Base):
    """IPO subscription / issue details from LLM (Gemini, etc.)."""

    __tablename__ = "ipo_llm_research"

    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    provider: Mapped[str] = mapped_column(String, default="gemini")
    status: Mapped[str] = mapped_column(String, default="fetched")  # fetched | failed
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
