from __future__ import annotations

from src.api.analysis_run_store import AnalysisRunStore
from src.api.dataset_store import DatasetStore
from src.services.chart_metrics import (
    build_metric_specs_from_chart_metrics,
    calculate_chart_metrics,
)
from src.services.processing_service import processing_service
from src.services.report_compiler import ReportCompiler
from src.utils.constants import STORE_MAX_ENTRIES, STORE_TTL_SECONDS

analysis_run_store = AnalysisRunStore(max_entries=STORE_MAX_ENTRIES, ttl_seconds=STORE_TTL_SECONDS)
dataset_store = DatasetStore(max_entries=STORE_MAX_ENTRIES, ttl_seconds=STORE_TTL_SECONDS)


def build_report_compiler() -> ReportCompiler:
    return ReportCompiler(
        processing_service=processing_service,
        calculate_chart_metrics=calculate_chart_metrics,
        build_metric_specs_from_chart_metrics=build_metric_specs_from_chart_metrics,
    )
