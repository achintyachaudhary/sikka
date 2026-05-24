"""IPO pattern research API (dataset + scikit-learn runs)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.ipo_research.dataset import dataset_stats, prepare_ipo_dataset
from app.services.ipo_research.ml_experiments import (
    ALGORITHM_CHOICES,
    TARGET_OPTIONS,
    get_run,
    list_runs,
    run_ml_experiment,
)

ipo_research_router = APIRouter(prefix="/api/ipo-research", tags=["ipo-research"])


class PrepareDataResponse(BaseModel):
    total_nse_ipos: int
    skipped_invalid_symbols: int = 0
    newly_enriched: int
    newly_saved: int
    skipped_cached: int
    failed_enrich: int
    no_market_data: int = 0
    total_dataset_rows: int
    pending_remaining: int


class DatasetStatsResponse(BaseModel):
    total_rows: int
    latest_built_at: str | None
    min_rows_for_ml: int
    ready_for_ml: bool


class RunExperimentRequest(BaseModel):
    algorithm: str = Field(
        default="all",
        description="all | random_forest | logistic_regression | gradient_boosting",
    )
    target: str = Field(
        default="profit_vs_issue",
        description="profit_listing_day | profit_vs_issue | strong_profit_vs_issue | profit_buy_listing_open",
    )
    prepare_data: bool = False
    force_data_refresh: bool = False


@ipo_research_router.get("/dataset/stats", response_model=DatasetStatsResponse)
def get_dataset_stats() -> DatasetStatsResponse:
    return DatasetStatsResponse(**dataset_stats())


@ipo_research_router.post("/dataset/prepare", response_model=PrepareDataResponse)
def prepare_dataset(
    force: bool = Query(False),
    batch_size: int = Query(40, ge=5, le=80),
) -> PrepareDataResponse:
    try:
        result = prepare_ipo_dataset(force_refresh=force, batch_size=batch_size)
        return PrepareDataResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@ipo_research_router.get("/runs")
def get_runs(limit: int = Query(50, ge=1, le=100)) -> dict:
    return {"runs": list_runs(limit=limit)}


@ipo_research_router.get("/runs/{run_id}")
def get_run_detail(run_id: int) -> dict:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@ipo_research_router.post("/runs")
def start_run(body: RunExperimentRequest) -> dict:
    if body.algorithm not in ALGORITHM_CHOICES:
        raise HTTPException(
            status_code=400,
            detail=f"algorithm must be one of: {', '.join(sorted(ALGORITHM_CHOICES))}",
        )
    if body.target not in TARGET_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"target must be one of: {', '.join(TARGET_OPTIONS.keys())}",
        )
    try:
        return run_ml_experiment(
            algorithm=body.algorithm,
            target_key=body.target,
            prepare_data=body.prepare_data,
            force_data_refresh=body.force_data_refresh,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@ipo_research_router.get("/algorithms")
def list_algorithms() -> dict:
    return {
        "algorithms": sorted(ALGORITHM_CHOICES),
        "targets": [
            {"id": k, "label": k.replace("_", " ").title()} for k in TARGET_OPTIONS
        ],
    }
