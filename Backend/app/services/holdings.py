"""Investor / shareholding data from NSE and yfinance."""

from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import requests
import yfinance as yf

from app.watchlists.loader import NSE_HEADERS

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "holdings"
CACHE_TTL = 86400 * 7  # 7 days

_memory: dict[str, tuple[float, dict]] = {}

SUMMARY_CONTEXT_SUFFIX = "_ContextI"
XBRL_CATEGORY_TAGS = {
    "promoter_holding_pct": "ShareholdingOfPromoterAndPromoterGroup",
    "fii_holding_pct": "InstitutionsForeign",
    "dii_holding_pct": "InstitutionsDomestic",
    "public_holding_pct": "PublicShareholding",
    "mutual_fund_holding_pct": "MutualFundsOrUTI",
}


def _nse_symbol(symbol: str) -> str:
    return symbol.upper().replace(".NS", "").replace(".BO", "")


def _parse_pct(value: str | float | None) -> float | None:
    if value is None:
        return None
    try:
        num = float(str(value).strip().replace(",", ""))
        if num > 100:
            return round(num, 2)
        if 0 <= num <= 1:
            return round(num * 100, 2)
        return round(num, 2)
    except (TypeError, ValueError):
        return None


def _parse_nse_date(raw: str) -> str | None:
    raw = (raw or "").strip()
    return raw if raw and raw != "-" else None


def _nse_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    session.headers["Referer"] = (
        "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern"
    )
    session.get("https://www.nseindia.com", timeout=15)
    return session


def _fetch_nse_master_list(nse_symbol: str) -> list[dict]:
    session = _nse_session()
    response = session.get(
        "https://www.nseindia.com/api/corporate-share-holdings-master",
        params={"index": "equities", "symbol": nse_symbol},
        timeout=20,
    )
    response.raise_for_status()
    rows = response.json()
    return rows if isinstance(rows, list) else []


def _fetch_nse_master(nse_symbol: str) -> dict | None:
    """Latest shareholding filing summary from NSE."""
    try:
        rows = _fetch_nse_master_list(nse_symbol)
        if not rows:
            return None

        def sort_key(row: dict) -> tuple:
            date = _parse_nse_date(row.get("date", "")) or ""
            return (date, row.get("submissionDate") or "")

        rows.sort(key=sort_key, reverse=True)
        latest = rows[0]
        xbrl = (latest.get("xbrl") or "").strip()
        if xbrl.endswith("/null") or xbrl == "null":
            xbrl = ""

        return {
            "promoter_holding_pct": _parse_pct(latest.get("pr_and_prgrp")),
            "public_holding_pct": _parse_pct(latest.get("public_val")),
            "holding_as_of": _parse_nse_date(latest.get("date", "")),
            "xbrl_url": xbrl or None,
        }
    except Exception:
        logger.exception("NSE shareholding master failed for %s", nse_symbol)
        return None


def _parse_xbrl_holdings(xbrl_url: str) -> dict[str, float | None]:
    """Extract category % from NSE shareholding XBRL (summary context)."""
    response = requests.get(xbrl_url, headers=NSE_HEADERS, timeout=45)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    tag_to_field = {v: k for k, v in XBRL_CATEGORY_TAGS.items()}
    result: dict[str, float | None] = {k: None for k in XBRL_CATEGORY_TAGS}

    for elem in root.iter():
        tag = elem.tag.split("}")[-1]
        if tag != "ShareholdingAsAPercentageOfTotalNumberOfShares":
            continue
        ctx = elem.get("contextRef", "")
        if not ctx.endswith(SUMMARY_CONTEXT_SUFFIX):
            continue
        category = ctx.removesuffix(SUMMARY_CONTEXT_SUFFIX)
        field = tag_to_field.get(category)
        if not field or not elem.text:
            continue
        pct = _parse_pct(elem.text)
        if pct is not None:
            result[field] = pct

    return result


def _fetch_yfinance_holdings(yf_symbol: str) -> dict[str, float | None]:
    try:
        info = yf.Ticker(yf_symbol).info
        inst = info.get("heldPercentInstitutions")
        insider = info.get("heldPercentInsiders")
        return {
            "institutional_holding_pct": round(inst * 100, 2) if inst is not None else None,
            "promoter_holding_pct": round(insider * 100, 2) if insider is not None else None,
        }
    except Exception:
        return {"institutional_holding_pct": None, "promoter_holding_pct": None}


def _cache_path(nse_symbol: str) -> Path:
    return CACHE_DIR / f"{nse_symbol}.json"


def _read_cache(nse_symbol: str) -> dict | None:
    path = _cache_path(nse_symbol)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
        if time.time() - payload.get("fetched_at", 0) > CACHE_TTL:
            return None
        return payload.get("data")
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(nse_symbol: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(nse_symbol).write_text(
        json.dumps({"fetched_at": time.time(), "data": data}, indent=0),
    )


def get_shareholding(symbol: str, *, fetch_xbrl: bool = True) -> dict:
    """
    Return holding percentages for a symbol.
    Prefers NSE quarterly filing (promoter / FII / DII / public); yfinance as fallback.
    Set fetch_xbrl=False for faster scans (promoter/public from NSE master only).
    """
    nse_symbol = _nse_symbol(symbol)
    yf_symbol = symbol if symbol.endswith((".NS", ".BO")) else f"{symbol}.NS"

    now = time.time()
    mem = _memory.get(nse_symbol)
    if mem and now < mem[0]:
        return mem[1].copy()

    cached = _read_cache(nse_symbol)
    if cached:
        _memory[nse_symbol] = (now + 300, cached)
        return cached.copy()

    data: dict[str, float | str | None] = {
        "promoter_holding_pct": None,
        "fii_holding_pct": None,
        "dii_holding_pct": None,
        "public_holding_pct": None,
        "mutual_fund_holding_pct": None,
        "institutional_holding_pct": None,
        "holding_as_of": None,
        "holding_source": None,
    }

    master = _fetch_nse_master(nse_symbol)
    if master:
        data["promoter_holding_pct"] = master.get("promoter_holding_pct")
        data["public_holding_pct"] = master.get("public_holding_pct")
        data["holding_as_of"] = master.get("holding_as_of")
        data["holding_source"] = "nse"

        xbrl_url = master.get("xbrl_url")
        if fetch_xbrl and xbrl_url:
            try:
                xbrl = _parse_xbrl_holdings(xbrl_url)
                for key, val in xbrl.items():
                    if val is not None:
                        data[key] = val
                data["holding_source"] = "nse_xbrl"
            except Exception:
                logger.warning("XBRL parse failed for %s", nse_symbol)

    yf = _fetch_yfinance_holdings(yf_symbol)
    if data["institutional_holding_pct"] is None:
        data["institutional_holding_pct"] = yf.get("institutional_holding_pct")
    if data["promoter_holding_pct"] is None:
        data["promoter_holding_pct"] = yf.get("promoter_holding_pct")
    if data["holding_source"] is None and (
        yf.get("institutional_holding_pct") is not None or yf.get("promoter_holding_pct") is not None
    ):
        data["holding_source"] = "yfinance"

    _write_cache(nse_symbol, data)
    _memory[nse_symbol] = (now + 300, data)
    return data.copy()


def _date_to_label(raw: str) -> str:
    """31-MAR-2026 -> Mar '26"""
    try:
        dt = datetime.strptime(raw.upper(), "%d-%b-%Y")
        return dt.strftime("%b '%y")
    except ValueError:
        return raw


def get_shareholding_history(symbol: str, max_periods: int = 5) -> list[dict]:
    """Historical quarterly shareholding from NSE XBRL filings."""
    nse_symbol = _nse_symbol(symbol)
    try:
        rows = _fetch_nse_master_list(nse_symbol)
    except Exception:
        logger.exception("NSE master list failed for %s", nse_symbol)
        return []

    def sort_key(row: dict) -> tuple:
        date = _parse_nse_date(row.get("date", "")) or ""
        return (date, row.get("submissionDate") or "")

    rows.sort(key=sort_key, reverse=True)

    seen_dates: set[str] = set()
    periods: list[dict] = []

    for row in rows:
        if len(periods) >= max_periods:
            break
        as_of = _parse_nse_date(row.get("date", ""))
        if not as_of or as_of in seen_dates:
            continue
        xbrl = (row.get("xbrl") or "").strip()
        if not xbrl or xbrl.endswith("/null") or xbrl.endswith("null"):
            continue

        seen_dates.add(as_of)
        entry: dict = {
            "as_of": as_of,
            "label": _date_to_label(as_of),
            "promoter_holding_pct": _parse_pct(row.get("pr_and_prgrp")),
            "public_holding_pct": _parse_pct(row.get("public_val")),
            "fii_holding_pct": None,
            "dii_holding_pct": None,
            "mutual_fund_holding_pct": None,
        }

        try:
            xbrl_data = _parse_xbrl_holdings(xbrl)
            for key, val in xbrl_data.items():
                if val is not None:
                    entry[key] = val
        except Exception:
            logger.warning("XBRL history parse failed for %s %s", nse_symbol, as_of)

        retail = entry.get("public_holding_pct")
        if retail is None and entry.get("promoter_holding_pct") is not None:
            inst = (entry.get("fii_holding_pct") or 0) + (entry.get("dii_holding_pct") or 0)
            prom = entry.get("promoter_holding_pct") or 0
            retail = round(max(0, 100 - prom - inst), 2)
        entry["retail_and_others_pct"] = retail

        periods.append(entry)

    periods.reverse()
    return periods
