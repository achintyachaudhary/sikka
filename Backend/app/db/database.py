"""SQLAlchemy engine, session factory, and declarative base."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{_DATA_DIR / 'app.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency for FastAPI route injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
