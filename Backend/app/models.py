"""Pydantic response schemas."""

from pydantic import BaseModel, Field


class StockSignal(BaseModel):
    symbol: str
    price: float
    change_5d_pct: float | None = None
    change_20d_pct: float | None = None
    rsi: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    score: int
    signals: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    trend: str = "neutral"


class PriceBar(BaseModel):
    date: str
    close: float


class StockDetail(StockSignal):
    history: list[PriceBar] = Field(default_factory=list)


class ScanResponse(BaseModel):
    scanned_at: str
    index: str
    index_label: str
    total_scanned: int
    total_matched: int
    min_score: int
    results: list[StockSignal]


class IndexOption(BaseModel):
    id: str
    label: str
    description: str
    slow_scan: bool = False


class IndicesResponse(BaseModel):
    indices: list[IndexOption]


class HealthResponse(BaseModel):
    status: str = "ok"
