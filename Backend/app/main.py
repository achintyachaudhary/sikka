"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.dashboard_routes import dashboard_router
from app.db.database import Base, engine
from app.utils.network import configure_market_data_network

# Must run before any yfinance / NSE HTTP calls (Cursor sets a local proxy that blocks Yahoo).
configure_market_data_network()

CORS_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app = FastAPI(
    title="NSE Stock Screener",
    description="Screen NSE stocks using RSI, MACD, SMA, and more.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _init_db() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(router)
app.include_router(dashboard_router)
