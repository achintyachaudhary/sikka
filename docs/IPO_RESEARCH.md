# IPO Research — Pattern Discovery (ML)

This document describes the **IPO Research** feature: building a historical IPO dataset, enriching it with market context, and running scikit-learn experiments to surface patterns related to profitable entry (educational only — **not financial advice**).

## Overview

| Step | What happens |
|------|----------------|
| **1. Prepare data** | Fetches **investor subscription times** (Gemini → `ipo_llm_research`), syncs Yahoo prices into **`ipo_listings`** (shared with IPO Tracker), then builds ML rows including subscription features. |
| **2. Market indices** | NIFTY, BANKNIFTY, SENSEX **1Y daily bars** in `market_index_cache` (used for returns & technicals before each listing). |
| **3. ML runs** | scikit-learn classifiers predict whether a defined “profit” target would have been met; feature importance and rule-based insights are saved per run. |
| **4. Portfolio sim** | If you invested ₹1 lakh in each IPO: total P&amp;L and portfolio ROI per scenario (issue→close, issue→today, etc.). |
| **5. UI** | **IPO Research** tab: prepare data, portfolio simulation, run algorithms, view run history. |

## Data sources

- **NSE** — `https://www.nseindia.com/api/public-past-issues` (full historical IPO list).
- **yfinance** — Post-listing OHLC for each symbol (`.NS` / `.BO`).
- **SQLite** — `ipo_llm_research` (subscription times from Gemini; fetched automatically during Prepare when `GEMINI_API_KEY` is set).
- **Market indices** — `^NSEI`, `^NSEBANK`, `^BSESN` via yfinance, cached in DB.

## Feature engineering

Per IPO row:

| Category | Features |
|----------|----------|
| **IPO** | `issue_price`, `issue_price_log`, `security_type_sme`, listing month/year |
| **Subscription** (Gemini / `ipo_llm_research`) | `overall_times_subscribed`, `overall_times_subscribed_log`, `qib_times_subscribed`, `nii_times_subscribed`, `retail_times_subscribed`, `employee_times_subscribed`, `qib_to_retail_ratio`, `has_subscription_data` |
| **Market (at listing)** | `nifty/banknifty/sensex_return_1w/1m/3m_before`, `market_avg_return_1m_before` |
| **Technical (NIFTY, via `ta`)** | `index_rsi_14`, `index_macd_hist` at listing |

### Targets (what “profit” means)

| Target ID | Meaning |
|-----------|---------|
| `profit_listing_day` | Listing close above issue price |
| `profit_vs_issue` | Current price above issue price |
| `strong_profit_vs_issue` | Gain vs issue ≥ 15% |
| `profit_buy_listing_open` | Gain from listing open to current |

Only features known **at or before** listing are used as model inputs (no leakage from future listing-day returns into features).

## Libraries used

| Library | Role |
|---------|------|
| **[scikit-learn](https://scikit-learn.org/)** | `RandomForestClassifier`, `LogisticRegression`, `GradientBoostingClassifier`, cross-validation, train/test split, pipelines with imputation + scaling |
| **[ta](https://github.com/bukosabino/ta)** | RSI & MACD on index series (standard technical analysis primitives) |
| **pandas / numpy** | Dataset tables and numerics |
| **yfinance** | Prices and index history |

There is **no** dedicated “stock market scikit-learn” package. Practice follows common quant/ML workflows:

- Label past outcomes (supervised learning).
- Use **market regime** features (index returns before IPO).
- Use **subscription demand** when available (similar to institutional interest proxies).
- Report **feature importance** and simple **conditional hit rates** (e.g. bull vs bear market).

For domain background, see NSE IPO disclosures, BSE listing norms, and general references on IPO underpricing and post-listing drift (academic literature; models here are simplified heuristics).

## Database tables

### `ipo_listings` (shared with IPO Tracker)

| Column | Description |
|--------|-------------|
| `symbol` | PK |
| `listing_date` | ISO date |
| `market_status` | `pending` / `listed` / `no_market_data` |
| `current_price`, gains | Yahoo enrichment (Tracker UI) |
| `features_json` / `targets_json` | ML inputs/labels (Research) |
| `ml_status` | `ready` when features built; `no_market_data` when Yahoo has no history |

**ML-ready count** equals IPOs with Yahoo prices in the chosen window — not every NSE row (recent listings often lack tradeable history yet).

Legacy `ipo_ml_features` is migrated into `ipo_listings` on startup.

### `ipo_research_runs`

| Column | Description |
|--------|-------------|
| `id` | PK |
| `algorithm` | `all`, `random_forest`, etc. |
| `status` | `running` / `completed` / `failed` |
| `metrics_json` | Sample count, best accuracy, positive rate |
| `insights_json` | Per-model metrics, top features, text insights |
| `summary_text` | Human-readable summary |
| `created_at` / `completed_at` | Run timestamps |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/ipo-research/dataset/stats` | Row counts, ready-for-ML flag |
| `GET` | `/api/ipo-research/portfolio-simulation?months=6&investment_inr=100000` | ₹1L-per-IPO ROI across entry/exit scenarios |
| `POST` | `/api/ipo-research/dataset/prepare?batch_size=40` | Enrich next batch (call until `pending_remaining` is 0) |
| `GET` | `/api/ipo-research/runs` | List past ML runs |
| `GET` | `/api/ipo-research/runs/{id}` | Run detail |
| `POST` | `/api/ipo-research/runs` | Start ML experiment |
| `GET` | `/api/ipo-research/algorithms` | List algorithms & targets |

### Example: start ML run

```json
POST /api/ipo-research/runs
{
  "algorithm": "all",
  "target": "profit_vs_issue",
  "prepare_data": false
}
```

## UI workflow

1. Open **IPO Research** in the sidebar.
2. Click **Prepare IPO data** — runs in batches (~40 IPOs per request); repeat until no pending rows remain (first full build can take several minutes).
3. Choose **algorithm** and **profit target**, click **Run scikit-learn analysis**.
4. Click a row in **Research runs** to see accuracy, top features, and pattern insights.

## Limitations

- **Survivorship / data quality** — Delisted or thinly traded names may lack yfinance history.
- **Subscription fetch** — Prepare pulls subscription data in batches (8 symbols per API call). Without `GEMINI_API_KEY`, ML runs without subscription features (`has_subscription_data=0`).
- **Non-stationary markets** — Past patterns may not repeat; accuracy is not a trading edge.
- **Not advice** — For research and learning only.

## File map

```
Backend/app/services/ipo_research/
  dataset.py           # NSE IPO load, enrich, DB cache
  market_features.py   # Index returns + ta indicators at listing
  ml_experiments.py    # scikit-learn pipelines + run persistence

Backend/app/api/ipo_research_routes.py
frontend/src/pages/IpoResearchPage.tsx
docs/IPO_RESEARCH.md   # this file
```

## Dependencies

Added to `Backend/requirements.txt`:

```
scikit-learn>=1.4
joblib>=1.3
```

Install:

```bash
cd Backend && pip install -r requirements.txt
```
