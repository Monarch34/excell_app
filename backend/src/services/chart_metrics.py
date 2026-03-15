from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd

from src.core.calculations import calculate_area, calculate_region_area
from src.core.charts.filtering import (
    apply_baseline_region_filter_df,
    apply_scope_filters,
    normalize_regions,
)
from src.domain.report_models import AnalysisMetricSpec


@dataclass
class ChartMetricResult:
    chart_id: str
    y_column: str | None
    area_total: float | None
    area_positive: float | None
    area_negative: float | None
    area_by_region: dict[str, float]


def _finite_or_none(value: float | int | None) -> float | None:
    if value is None:
        return None
    as_float = float(value)
    if not math.isfinite(as_float):
        return None
    return as_float


def _finite_or_default(value: float | int | None, default: float) -> float:
    finite = _finite_or_none(value)
    return default if finite is None else finite


def _sanitize_area_by_region(values: dict[str, float]) -> dict[str, float]:
    sanitized: dict[str, float] = {}
    for region, value in values.items():
        finite = _finite_or_none(value)
        if finite is None:
            continue
        sanitized[region] = finite
    return sanitized


def calculate_chart_metrics(df: pd.DataFrame, charts: list[Any]) -> list[ChartMetricResult]:
    """Calculate chart metrics for all configured charts."""
    all_metrics: list[ChartMetricResult] = []

    for chart in charts:
        if not chart.x_column or not chart.y_columns:
            continue

        for y_column in chart.y_columns:
            if chart.x_column not in df.columns or y_column not in df.columns:
                continue

            filtered_df = apply_scope_filters(
                df,
                x_column=chart.x_column,
                y_column=y_column,
                scope=chart.scope,
            )

            selected_regions = normalize_regions(
                chart.baseline_spec.regions if chart.baseline_spec else []
            )
            if chart.baseline_spec and selected_regions:
                filtered_df = apply_baseline_region_filter_df(
                    filtered_df,
                    x_column=chart.x_column,
                    y_column=y_column,
                    regions=selected_regions,
                    x_baseline=chart.baseline_spec.x_baseline,
                    y_baseline=chart.baseline_spec.y_baseline,
                )

            x_values = pd.to_numeric(filtered_df[chart.x_column], errors="coerce").to_numpy()
            y_values = pd.to_numeric(filtered_df[y_column], errors="coerce").to_numpy()

            area_total = None
            area_positive = None
            area_negative = None
            area_by_region: dict[str, float] = {}
            custom_label = (
                str(chart.area_spec.label).strip()
                if chart.area_spec and chart.area_spec.label is not None
                else ""
            )

            if (
                chart.chart_type == "area"
                and chart.area_spec
                and chart.area_spec.y_column == y_column
                and custom_label
            ):
                baseline = (
                    _finite_or_default(getattr(chart.baseline_spec, "y_baseline", None), 0.0)
                    if chart.baseline_spec
                    else _finite_or_default(getattr(chart.area_spec, "baseline", None), 0.0)
                )
                if not selected_regions:
                    area_total = _finite_or_none(
                        calculate_area(x_values, y_values, chart.area_spec.mode, baseline)
                    )
                else:
                    x_baseline = (
                        _finite_or_default(getattr(chart.baseline_spec, "x_baseline", None), 0.0)
                        if chart.baseline_spec
                        else 0.0
                    )
                    for region in selected_regions:
                        area_by_region[region] = calculate_region_area(
                            x_values, y_values, x_baseline, baseline, region
                        )
                    area_by_region = _sanitize_area_by_region(area_by_region)
                    area_total = _finite_or_none(sum(area_by_region.values()))

                    top_regions = [
                        value
                        for region, value in area_by_region.items()
                        if region.startswith("top-")
                    ]
                    bottom_regions = [
                        value
                        for region, value in area_by_region.items()
                        if region.startswith("bottom-")
                    ]
                    if top_regions:
                        area_positive = _finite_or_none(sum(top_regions))
                    if bottom_regions:
                        area_negative = _finite_or_none(sum(abs(v) for v in bottom_regions))

            if (
                area_total is None
                and area_positive is None
                and area_negative is None
                and len(area_by_region) == 0
            ):
                continue

            all_metrics.append(
                ChartMetricResult(
                    chart_id=chart.id,
                    y_column=y_column,
                    area_total=area_total,
                    area_positive=area_positive,
                    area_negative=area_negative,
                    area_by_region=area_by_region,
                )
            )

    return all_metrics


def build_metric_specs_from_chart_metrics(
    chart_metrics: list[ChartMetricResult],
    charts: list[Any],
) -> list[AnalysisMetricSpec]:
    chart_by_id = {chart.id: chart for chart in charts}
    payload: list[AnalysisMetricSpec] = []

    for metric in chart_metrics:
        chart = chart_by_id.get(metric.chart_id)
        if chart is None:
            continue

        chart_title = chart.title or ""
        fallback_y = (
            chart.area_spec.y_column
            if chart.area_spec
            else (chart.y_columns[0] if chart.y_columns else "")
        )
        y_column = metric.y_column or fallback_y

        if metric.area_total is not None:
            custom_label = (
                str(chart.area_spec.label).strip()
                if chart.area_spec and chart.area_spec.label is not None
                else ""
            )
            if not custom_label:
                continue
            payload.append(
                AnalysisMetricSpec(
                    chart_id=metric.chart_id,
                    chart_title=chart_title,
                    name=custom_label,
                    value=metric.area_total,
                    unit="",
                    x_column=chart.x_column,
                    y_column=y_column,
                )
            )

    return payload
