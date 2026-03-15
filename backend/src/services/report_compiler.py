"""
Report Compiler service.

Compiles an ExportRequest DTO into a fully prepared report payload:
- processed/export DataFrame
- calculated metric specs
- generated chart images
- builder-ready metadata and layout

The compile pipeline is split into focused compilers that the
ExportOrchestrator (``ReportCompiler.compile``) coordinates:

- **DataCompiler**  — runs the processing pipeline and selects export columns.
- **MetricsCompiler** — builds metric specs from request + chart-level calculations.
- **ChartImageCompiler** — generates chart PNGs (parallelised via ThreadPoolExecutor).
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

from src.core.formulas.engine import UserFormula
from src.domain.report_models import AnalysisMetricSpec, DerivedColumnSpec, ParameterSpec
from src.services.chart_generator import ChartGenerator
from src.services.processing_service import ProcessingService
from src.utils.helpers import normalize_hex_color as normalize_hex_color_value
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.api.schemas import ExportRequest

logger = get_logger(__name__)

MetricCalculator = Callable[[pd.DataFrame, list[Any]], list[Any]]
MetricSpecBuilder = Callable[[list[Any], list[Any]], list[AnalysisMetricSpec]]


@dataclass
class CompiledExportReport:
    export_df: pd.DataFrame
    column_units: dict[str, str]
    derived_specs: list[DerivedColumnSpec]
    metric_specs: list[AnalysisMetricSpec]
    parameter_specs: list[ParameterSpec]
    chart_images: list[tuple]
    column_layout: dict[str, Any] | None
    header_mapping: dict[str, str]
    column_colors: dict[str, str]
    project_name: str


# ---------------------------------------------------------------------------
# Focused compilers
# ---------------------------------------------------------------------------


def _safe_dump(model: Any) -> Any:
    if model is None:
        return None
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return model


def _resolve_chart_type(raw_chart_type: str | None, has_area_spec: bool) -> str:
    chart_type = (raw_chart_type or "").strip().lower()
    if chart_type in {"line", "scatter", "area"}:
        return chart_type
    return "area" if has_area_spec else "line"


def _normalize_hex_color(value: Any) -> str | None:
    return normalize_hex_color_value(value)


class DataCompiler:
    """Runs the processing pipeline and selects export columns."""

    def __init__(self, processing_service: ProcessingService) -> None:
        self._processing_service = processing_service

    def compile(
        self,
        request: ExportRequest,
        source_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int | str | bool | None]]:
        """Returns (processed_df, export_df, results)."""
        header_mapping = request.header_mapping or {}
        operations = [{"type": op.type, "config": op.config} for op in request.operations]
        formulas = [
            UserFormula(
                name=dc.name,
                formula=dc.formula,
                unit=dc.unit,
                description=dc.description,
            )
            for dc in request.derived_columns
            if dc.enabled
        ]
        derived_parameters = [
            {"name": dp.name, "formula": dp.formula}
            for dp in request.derived_parameters
        ]
        initial_results = (
            {"manual_reference_index": request.reference_index}
            if request.reference_index is not None
            else {}
        )

        processed_df, results = self._processing_service.process(
            df=source_df,
            operations=operations,
            formulas=formulas,
            parameters=request.parameters,
            column_mapping=request.column_mapping or None,
            derived_parameters=derived_parameters,
            initial_results=initial_results,
            header_mapping=header_mapping,
        )

        selected = request.selected_columns
        derived_names = [dc.name for dc in request.derived_columns if dc.enabled]
        all_cols = [c for c in selected + derived_names if c in processed_df.columns]
        export_df = processed_df[all_cols] if all_cols else processed_df

        return processed_df, export_df, results


class MetricsCompiler:
    """Builds metric specs from request metrics and chart-level calculations."""

    def __init__(
        self,
        calculate_chart_metrics: MetricCalculator,
        build_metric_specs_from_chart_metrics: MetricSpecBuilder,
    ) -> None:
        self._calculate = calculate_chart_metrics
        self._build_specs = build_metric_specs_from_chart_metrics

    def compile(
        self,
        request: ExportRequest,
        chart_df: pd.DataFrame,
        results: dict[str, float | int | str | bool | None],
    ) -> list[AnalysisMetricSpec]:
        specs: list[AnalysisMetricSpec] = [
            AnalysisMetricSpec(
                chart_id=m.chart_id,
                chart_title=m.chart_title,
                name=m.name,
                value=m.value,
                unit=m.unit,
                x_column=m.x_column,
                y_column=m.y_column,
            )
            for m in request.metrics
        ]

        if request.charts:
            computed = self._calculate(chart_df, request.charts)
            computed_specs = self._build_specs(computed, request.charts)
            existing_keys = {(m.chart_id, m.name, m.y_column) for m in specs}
            for m in computed_specs:
                key = (m.chart_id, m.name, m.y_column)
                if key not in existing_keys:
                    specs.append(m)
                    existing_keys.add(key)

        existing_parameter_names = {metric.name for metric in specs if not metric.chart_id}
        for derived_parameter in request.derived_parameters:
            name = derived_parameter.name
            if name in existing_parameter_names:
                continue
            value = results.get(name)
            if isinstance(value, int | float):
                specs.append(
                    AnalysisMetricSpec(
                        chart_id="",
                        chart_title="",
                        name=name,
                        value=float(value),
                        unit=request.parameter_units.get(name, ""),
                        x_column="",
                        y_column="",
                    )
                )
                existing_parameter_names.add(name)

        return specs


class ChartImageCompiler:
    """Generates chart PNGs, parallelised via ThreadPoolExecutor."""

    MAX_WORKERS = 4

    def __init__(self, chart_generator: ChartGenerator | None = None) -> None:
        self._generator = chart_generator or ChartGenerator()

    def _render_single(self, chart: Any, chart_df: pd.DataFrame) -> tuple[str, Any]:
        title = chart.title or f"Chart {chart.id}"
        try:
            area_spec_dict = _safe_dump(chart.area_spec) if chart.area_spec else None
            chart_type = _resolve_chart_type(chart.chart_type, area_spec_dict is not None)
            spec = {
                "title": chart.title,
                "x_column": chart.x_column,
                "y_columns": chart.y_columns,
                "chart_type": chart_type,
                "x_axis_label": chart.x_axis_label,
                "y_axis_label": chart.y_axis_label,
                "line_color": chart.line_color,
                "fill_color": chart.fill_color,
                "fill_opacity": chart.fill_opacity,
                "line_width": chart.line_width,
                "marker_size": chart.marker_size,
                "area_spec": area_spec_dict,
                "baseline_spec": _safe_dump(chart.baseline_spec),
                "scope": _safe_dump(chart.scope),
                "annotations": [_safe_dump(a) for a in chart.annotations]
                if chart.annotations
                else [],
            }
            buf = self._generator.generate_from_spec(chart_df, spec)
            return (title, buf)
        except Exception as exc:
            logger.error(f"Chart generation failed for '{title}': {exc}")
            logger.error(traceback.format_exc())
            try:
                fallback = self._generator.generate_error_placeholder(title, str(exc))
                return (title, fallback)
            except Exception as placeholder_exc:
                logger.warning(
                    f"Chart '{title}' dropped: both generation and error placeholder failed. "
                    f"Placeholder error: {placeholder_exc}"
                )
                return (title, None)

    def compile(self, request: ExportRequest, chart_df: pd.DataFrame) -> list[tuple]:
        if not request.charts:
            return []

        workers = min(self.MAX_WORKERS, len(request.charts))
        if workers <= 1:
            results = [self._render_single(c, chart_df) for c in request.charts]
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = [
                    pool.submit(self._render_single, chart, chart_df)
                    for chart in request.charts
                ]
                results = [f.result() for f in futures]

        return [(title, buf) for title, buf in results if buf is not None]


# ---------------------------------------------------------------------------
# Orchestrator (preserves the original ReportCompiler interface)
# ---------------------------------------------------------------------------


class ReportCompiler:
    """
    Orchestrates DataCompiler, MetricsCompiler, and ChartImageCompiler to
    produce a ``CompiledExportReport``.
    """

    def __init__(
        self,
        *,
        processing_service: ProcessingService,
        calculate_chart_metrics: MetricCalculator,
        build_metric_specs_from_chart_metrics: MetricSpecBuilder,
    ) -> None:
        self._data_compiler = DataCompiler(processing_service)
        self._metrics_compiler = MetricsCompiler(
            calculate_chart_metrics, build_metric_specs_from_chart_metrics
        )
        self._chart_compiler = ChartImageCompiler()

    def compile(self, request: ExportRequest, *, source_df: pd.DataFrame) -> CompiledExportReport:
        header_mapping = request.header_mapping or {}

        # 1. Data processing
        processed_df, export_df, results = self._data_compiler.compile(request, source_df)

        # 2. Build specs
        column_units = dict(request.units)
        for dc in request.derived_columns:
            if dc.unit:
                column_units[dc.name] = dc.unit

        derived_specs = [
            DerivedColumnSpec(
                name=dc.name,
                formula=dc.formula,
                unit=dc.unit,
                description=dc.description,
                dependencies=", ".join(dc.dependencies),
                enabled=dc.enabled,
            )
            for dc in request.derived_columns
        ]

        parameter_specs = [
            ParameterSpec(name=k, value=v, unit=request.parameter_units.get(k, ""))
            for k, v in request.parameters.items()
        ]
        existing_parameter_names = {p.name for p in parameter_specs}
        for dp in request.derived_parameters:
            if dp.name in existing_parameter_names:
                continue
            value = results.get(dp.name)
            if isinstance(value, int | float):
                parameter_specs.append(
                    ParameterSpec(
                        name=dp.name,
                        value=float(value),
                        unit=request.parameter_units.get(dp.name, ""),
                    )
                )
                existing_parameter_names.add(dp.name)

        # 3. Chart-specific data slicing
        chart_df = processed_df
        if request.reference_index is not None and request.reference_index > 0:
            if request.reference_index >= len(processed_df):
                chart_df = processed_df.iloc[0:0]
            else:
                chart_df = processed_df.iloc[request.reference_index:]

        # 4. Metrics and chart images
        metric_specs = self._metrics_compiler.compile(request, chart_df, results)
        chart_images = self._chart_compiler.compile(request, chart_df)

        # 5. Layout and colors
        column_layout = None
        matching_groups: list[Any] = []
        if request.column_layout:
            matching_groups = list(request.column_layout.matching_groups or [])
            column_layout = {
                "column_order": request.column_layout.column_order,
                "linked_groups": request.column_layout.linked_groups,
                "matching_groups": matching_groups,
                "separator_indices": request.column_layout.separator_indices,
                "separator_color": request.column_layout.separator_color,
            }

        column_colors: dict[str, str] = {}
        for column_name, color in (request.column_colors or {}).items():
            normalized = _normalize_hex_color(color)
            if normalized:
                column_colors[column_name] = normalized

        for group in matching_groups:
            normalized = _normalize_hex_color(getattr(group, "color", None))
            if not normalized:
                continue
            for column_name in getattr(group, "columns", []) or []:
                column_colors.setdefault(column_name, normalized)

        return CompiledExportReport(
            export_df=export_df,
            column_units=column_units,
            derived_specs=derived_specs,
            metric_specs=metric_specs,
            parameter_specs=parameter_specs,
            chart_images=chart_images,
            column_layout=column_layout,
            header_mapping=header_mapping,
            column_colors=column_colors,
            project_name=request.project_name,
        )
