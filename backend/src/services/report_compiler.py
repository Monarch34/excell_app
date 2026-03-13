"""
Report Compiler service.

Compiles an ExportRequest DTO into a fully prepared report payload:
- processed/export DataFrame
- calculated metric specs
- generated chart images
- builder-ready metadata and layout
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pandas as pd

from src.core.formulas.engine import UserFormula
from src.services.chart_generator import ChartGenerator
from src.services.processing_service import ProcessingService
from src.services.xlsx_report_builder import AnalysisMetricSpec, DerivedColumnSpec, ParameterSpec
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


class ReportCompiler:
    """
    Compiles export DTO data into builder-ready structures.
    """

    def __init__(
        self,
        *,
        processing_service: ProcessingService,
        calculate_chart_metrics: MetricCalculator,
        build_metric_specs_from_chart_metrics: MetricSpecBuilder,
    ) -> None:
        self.processing_service = processing_service
        self.calculate_chart_metrics = calculate_chart_metrics
        self.build_metric_specs_from_chart_metrics = build_metric_specs_from_chart_metrics
        self.chart_generator = ChartGenerator()

    @staticmethod
    def _safe_dump(model: Any) -> Any:
        if model is None:
            return None
        if hasattr(model, "model_dump"):
            return model.model_dump()
        if hasattr(model, "dict"):
            return model.dict()
        return model

    @staticmethod
    def _resolve_chart_type(raw_chart_type: str | None, has_area_spec: bool) -> str:
        chart_type = (raw_chart_type or "").strip().lower()
        if chart_type in {"line", "scatter", "area"}:
            return chart_type
        return "area" if has_area_spec else "line"

    @staticmethod
    def _normalize_hex_color(value: Any) -> str | None:
        return normalize_hex_color_value(value)

    def _build_export_df(self, request: ExportRequest, processed_df: pd.DataFrame) -> pd.DataFrame:
        selected = request.selected_columns
        derived_names = [dc.name for dc in request.derived_columns if dc.enabled]
        all_cols = [c for c in selected + derived_names if c in processed_df.columns]
        if all_cols:
            return processed_df[all_cols]
        return processed_df

    def _build_metric_specs(
        self, request: ExportRequest, chart_df: pd.DataFrame
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
            computed = self.calculate_chart_metrics(chart_df, request.charts)
            computed_specs = self.build_metric_specs_from_chart_metrics(computed, request.charts)
            existing_keys = {(m.chart_id, m.name, m.y_column) for m in specs}
            for m in computed_specs:
                key = (m.chart_id, m.name, m.y_column)
                if key in existing_keys:
                    continue
                specs.append(m)
                existing_keys.add(key)

        return specs

    def _build_chart_images(self, request: ExportRequest, chart_df: pd.DataFrame) -> list[tuple]:
        chart_images: list[tuple] = []

        for chart in request.charts:
            try:
                area_spec_dict = self._safe_dump(chart.area_spec) if chart.area_spec else None
                chart_type = self._resolve_chart_type(chart.chart_type, area_spec_dict is not None)
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
                    "baseline_spec": self._safe_dump(chart.baseline_spec),
                    "scope": self._safe_dump(chart.scope),
                    "annotations": [self._safe_dump(a) for a in chart.annotations]
                    if chart.annotations
                    else [],
                }
                buf = self.chart_generator.generate_from_spec(chart_df, spec)
                chart_images.append((chart.title or f"Chart {chart.id}", buf))
            except Exception as exc:
                logger.error(f"Chart generation failed for '{chart.title}': {exc}")
                logger.error(traceback.format_exc())
                try:
                    fallback = self.chart_generator.generate_error_placeholder(
                        chart.title or f"Chart {chart.id}",
                        str(exc),
                    )
                    chart_images.append((chart.title or f"Chart {chart.id}", fallback))
                except Exception:
                    continue

        return chart_images

    def _append_missing_derived_parameter_metrics(
        self,
        specs: list[AnalysisMetricSpec],
        request: ExportRequest,
        results: dict[str, float | int | str | bool | None],
    ) -> list[AnalysisMetricSpec]:
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

    def compile(self, request: ExportRequest, *, source_df: pd.DataFrame) -> CompiledExportReport:
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
            {
                "name": dp.name,
                "formula": dp.formula,
            }
            for dp in request.derived_parameters
        ]
        initial_results = (
            {"manual_reference_index": request.reference_index}
            if request.reference_index is not None
            else {}
        )

        processed_df, results = self.processing_service.process(
            df=source_df,
            operations=operations,
            formulas=formulas,
            parameters=request.parameters,
            column_mapping=request.column_mapping or None,
            derived_parameters=derived_parameters,
            initial_results=initial_results,
            header_mapping=header_mapping,
        )

        chart_source_df = processed_df
        export_df = self._build_export_df(request, processed_df)

        # Units and builder specs
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
        existing_parameter_names = {parameter.name for parameter in parameter_specs}
        for derived_parameter in request.derived_parameters:
            name = derived_parameter.name
            if name in existing_parameter_names:
                continue
            value = results.get(name)
            if isinstance(value, int | float):
                parameter_specs.append(
                    ParameterSpec(
                        name=name,
                        value=float(value),
                        unit=request.parameter_units.get(name, ""),
                    )
                )
                existing_parameter_names.add(name)

        chart_df = chart_source_df
        if request.reference_index is not None and request.reference_index > 0:
            if request.reference_index >= len(chart_source_df):
                chart_df = chart_source_df.iloc[0:0]
            else:
                chart_df = chart_source_df.iloc[request.reference_index :]

        metric_specs = self._build_metric_specs(request, chart_df)
        metric_specs = self._append_missing_derived_parameter_metrics(
            metric_specs,
            request,
            results,
        )
        chart_images = self._build_chart_images(request, chart_df)

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

        # Prefer explicit per-column colors from frontend. Fallback derives
        # colors from matching groups for robustness.
        column_colors: dict[str, str] = {}
        for column_name, color in (request.column_colors or {}).items():
            normalized = self._normalize_hex_color(color)
            if normalized:
                column_colors[column_name] = normalized

        for group in matching_groups:
            normalized = self._normalize_hex_color(getattr(group, "color", None))
            if not normalized:
                continue
            for column_name in getattr(group, "columns", []) or []:
                # Keep first explicit assignment stable.
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
