from __future__ import annotations

import asyncio
from dataclasses import asdict

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from src.api.analysis_run_store import AnalysisRunStore
from src.api.dependencies import get_analysis_run_store
from src.api.schemas import CalculateMetricsRequest, CalculateMetricsResponse, ChartMetrics
from src.services.chart_metrics import calculate_chart_metrics
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/charts", tags=["charts"])


@router.post("/metrics", response_model=CalculateMetricsResponse)
async def calculate_metrics(
    request: CalculateMetricsRequest,
    run_store: AnalysisRunStore = Depends(get_analysis_run_store),
):
    """Calculate chart metrics for configured area charts with named outputs."""
    try:
        source_data = request.data
        if source_data is None:
            if not request.run_id:
                raise ValueError("Either 'data' or 'run_id' must be provided")
            source_data = run_store.get_processed_data(request.run_id)
            if source_data is None:
                raise ValueError(f"Unknown or expired analysis run id: {request.run_id}")

        if len(source_data) > 50_000:
            raise ValueError(
                f"Dataset too large for metrics calculation ({len(source_data)} rows). "
                f"Maximum is 50,000 rows."
            )

        df = pd.DataFrame(source_data)
        metrics = await asyncio.to_thread(calculate_chart_metrics, df, request.charts)
        logger.info(f"Calculated metrics for {len(metrics)} chart configurations")
        return CalculateMetricsResponse(
            metrics=[ChartMetrics(**asdict(metric)) for metric in metrics]
        )
    except ValueError as exc:
        logger.error(f"Metrics calculation failed: {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
