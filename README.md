# 75ruppee_gain — NSE Stock Screener

Monorepo with a **FastAPI backend** and **React frontend** that screens Nifty 50 stocks using yfinance and technical indicators (RSI, MACD, SMA).

**Not financial advice.** For education and screening only.

## Project layout

```
75ruppee_gain/
├── Backend/          # FastAPI + yfinance screener API
└── frontend/         # React dashboard (Vite)
```

## Setup

### Backend

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run (two terminals)

**Terminal 1 — API (port 8000):**

```bash
cd Backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — React (port 5173):**

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** for the dashboard. API docs: **http://127.0.0.1:8000/docs**

The Vite dev server proxies `/api` and `/health` to the backend.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness check |
| `GET /api/indices` | Available watchlists (Nifty 50/100/200/500, all NSE EQ) |
| `GET /api/scan?index=nifty50&min_score=5&limit=100` | Scan selected index for bullish stocks |
| `GET /api/stock/{symbol}` | Single stock detail (e.g. `RELIANCE.NS`) |

## Configuration

- Indicator thresholds: `Backend/app/config.py`
- Index symbols: fetched from NSE archives (`nsearchives.nseindia.com`), cached 24h in `Backend/data/cache/`
- Scan `index` values: `nifty50`, `nifty100`, `nifty200`, `nifty500`, `nse_all`
- CORS origins: set `CORS_ORIGINS` (default allows Vite on port 5173)

## Limitations

- Nifty 50 scan ~1–2 min; Nifty 500 several minutes; **all NSE (~2100 stocks) can take 30–60+ minutes**.
- Scan results cached 15 minutes per index on the backend.
- yfinance data may be delayed or incomplete.
