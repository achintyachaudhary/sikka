"""Lightweight SQLite migrations (add columns without Alembic)."""

from sqlalchemy import inspect, text

from app.db.database import engine


def migrate_ipo_llm_research() -> None:
    insp = inspect(engine)
    if "ipo_llm_research" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("ipo_llm_research")}
    with engine.begin() as conn:
        if "status" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE ipo_llm_research "
                    "ADD COLUMN status VARCHAR NOT NULL DEFAULT 'fetched'"
                )
            )
        if "error_message" not in cols:
            conn.execute(
                text("ALTER TABLE ipo_llm_research ADD COLUMN error_message TEXT")
            )
        # Backfill legacy rows
        conn.execute(
            text(
                "UPDATE ipo_llm_research SET status = 'fetched' "
                "WHERE status IS NULL OR status = ''"
            )
        )


def migrate_ipo_ml_features() -> None:
    insp = inspect(engine)
    if "ipo_ml_features" not in insp.get_table_names():
        return

    cols = {c["name"] for c in insp.get_columns("ipo_ml_features")}
    with engine.begin() as conn:
        if "enrichment_status" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE ipo_ml_features "
                    "ADD COLUMN enrichment_status VARCHAR NOT NULL DEFAULT 'ready'"
                )
            )
        conn.execute(
            text(
                "UPDATE ipo_ml_features SET enrichment_status = 'ready' "
                "WHERE enrichment_status IS NULL OR enrichment_status = ''"
            )
        )


def migrate_ipo_listings() -> None:
    """Create ipo_listings and copy legacy ipo_ml_features rows."""
    import app.db.models as _models  # noqa: F401 — register tables

    _models.IpoListing.__table__.create(bind=engine, checkfirst=True)

    insp = inspect(engine)
    if "ipo_listings" not in insp.get_table_names():
        return

    # Copy from ipo_ml_features if present
    if "ipo_ml_features" in insp.get_table_names():
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT OR IGNORE INTO ipo_listings (
                        symbol, company_name, listing_date, features_json, targets_json,
                        ml_status, ml_built_at, market_status, updated_at
                    )
                    SELECT symbol, company_name, listing_date, features_json, targets_json,
                           CASE enrichment_status
                             WHEN 'ready' THEN 'ready'
                             WHEN 'no_market_data' THEN 'no_market_data'
                             ELSE 'incomplete'
                           END,
                           built_at,
                           CASE enrichment_status
                             WHEN 'no_market_data' THEN 'no_market_data'
                             ELSE 'listed'
                           END,
                           built_at
                    FROM ipo_ml_features
                    """
                )
            )
