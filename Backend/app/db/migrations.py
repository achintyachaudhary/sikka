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
