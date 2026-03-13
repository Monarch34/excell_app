from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

# Shared request models


class OperationSpec(BaseModel):
    """A generic data operation to execute in the processing pipeline."""

    type: str = Field(
        ..., description="Operation type (find_zero, slice_from_index, offset_correction)"
    )
    config: dict[str, Any] = Field(
        default_factory=dict, description="Operation-specific configuration"
    )


class UserFormulaModel(BaseModel):
    name: str
    formula: str
    unit: str = ""
    description: str = ""
    enabled: bool = True


class DerivedParameterDef(BaseModel):
    """A scalar value computed from input parameters before formula evaluation."""

    name: str = Field(..., description="Variable name (e.g., 'A0')")
    formula: str = Field(
        ..., description="Formula using parameter names (e.g., 'width * thickness')"
    )


class ComputationContextBase(BaseModel):
    """Shared computation context for processing, preview, and export endpoints."""

    dataset_id: str = Field(..., description="Uploaded dataset identifier")
    parameters: dict[str, float] = Field(
        default_factory=dict, description="Test parameters (e.g., length, width, thickness)"
    )
    column_mapping: dict[str, str] | None = Field(
        default=None, description="Mapping of logical columns to CSV columns"
    )
    user_formulas: list[UserFormulaModel] = Field(default_factory=list)
    derived_parameters: list[DerivedParameterDef] = Field(
        default_factory=list, description="Derived parameters to compute before formulas"
    )
    header_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Column key -> display label mapping for formula alias resolution",
    )


# Processing schemas


class ProcessRequest(ComputationContextBase):
    project_name: str = "Analysis"
    units: dict[str, str] = Field(default_factory=dict)
    operations: list[OperationSpec] = Field(
        default_factory=list, description="Generic operations to execute before formulas"
    )
    column_mapping: dict[str, str] = Field(
        default_factory=dict, description="Mapping of logical columns to CSV columns"
    )
    initial_results: dict[str, float | int | str | bool | None] = Field(
        default_factory=dict,
        description="Pre-computed values to inject into operation results (e.g., manual_reference_index)",
    )


class ProcessResponse(BaseModel):
    processed_data: list[dict[str, Any]] | None = None
    results: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
    project_name: str
    units: dict[str, str]
    run_id: str


# Formula preview schemas


class FormulaPreviewRequest(ComputationContextBase):
    formula: str
    target_type: Literal["column", "parameter"] = "column"
    sample_start: int = Field(
        default=0, ge=0, le=1_000_000, description="Starting row index for preview window"
    )
    sample_size: int = Field(
        default=50, ge=1, le=5000, description="Maximum preview rows to evaluate"
    )
    reference_index: int | None = Field(
        None, ge=0, description="Reference row index for REF() function"
    )


class FormulaPreviewResponse(BaseModel):
    success: bool
    values: list[float] = Field(default_factory=list)
    is_scalar: bool = False
    error: str | None = None
    error_code: Literal["division", "variable", "syntax", "dataset_expired", "generic"] | None = (
        None
    )


# Export and chart schemas


class BaselineSpecModel(BaseModel):
    """Baseline configuration for area calculations."""

    x_baseline: float = 0.0
    y_baseline: float = 0.0
    regions: list[str] = Field(
        default_factory=list,
        description="Selected regions: 'top-left', 'top-right', 'bottom-left', 'bottom-right', or 'all'",
    )


class ChartScopeModel(BaseModel):
    """Data filtering scope for chart."""

    mode: Literal["range"] | None = None
    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None


class AnnotationModel(BaseModel):
    """Chart annotation marker."""

    x: float
    y: float
    text: str
    show_arrow: bool = True


class AreaSpecModel(BaseModel):
    mode: Literal["positive", "negative", "total"]
    baseline: float = 0.0
    x_column: str
    y_column: str
    label: str | None = None


class ChartSpecModel(BaseModel):
    id: str
    title: str = ""
    x_column: str
    y_columns: list[str] = Field(default_factory=list)
    chart_type: Literal["line", "scatter", "area"] = "line"
    x_axis_label: str | None = None
    y_axis_label: str | None = None
    area_spec: AreaSpecModel | None = None
    baseline_spec: BaselineSpecModel | None = None
    line_color: str | None = None
    fill_color: str | None = None
    fill_opacity: float | None = 0.4
    line_width: float | None = None
    marker_size: float | None = None
    scope: ChartScopeModel | None = None
    annotations: list[AnnotationModel] = Field(default_factory=list)


class AnalysisMetricModel(BaseModel):
    id: str = ""
    chart_id: str = ""
    chart_title: str = ""
    name: str
    value: float
    unit: str = ""
    x_column: str = ""
    y_column: str = ""


class MatchingGroupSpecModel(BaseModel):
    """Column matching group used for export coloring."""

    id: str | None = None
    name: str = ""
    color: str = ""
    columns: list[str] = Field(default_factory=list)


class ColumnLayoutSpec(BaseModel):
    """Column ordering, grouping, and separator specification."""

    column_order: list[str] = Field(default_factory=list)
    linked_groups: list[list[str]] = Field(default_factory=list)
    matching_groups: list[MatchingGroupSpecModel] = Field(default_factory=list)
    separator_indices: list[int] = Field(default_factory=list)
    separator_color: str | None = None


class DerivedColumnModel(BaseModel):
    id: str
    name: str
    formula: str
    unit: str = ""
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)
    enabled: bool = True


class ExportRequest(ComputationContextBase):
    """Extended export request for the 4-sheet XLSX report."""

    units: dict[str, str] = Field(default_factory=dict)
    operations: list[OperationSpec] = Field(
        default_factory=list, description="Generic operations to execute before formulas"
    )
    project_name: str = "Report"
    schema_version: str = Field("1.0", description="Export DTO schema version")
    selected_columns: list[str] = Field(default_factory=list)
    derived_columns: list[DerivedColumnModel] = Field(default_factory=list)
    charts: list[ChartSpecModel] = Field(default_factory=list)
    metrics: list[AnalysisMetricModel] = Field(default_factory=list)
    custom_filename: str | None = None
    column_layout: ColumnLayoutSpec | None = None
    column_colors: dict[str, str] = Field(
        default_factory=dict, description="Column name -> hex color (e.g. 'D6EAF8')"
    )
    parameter_units: dict[str, str] = Field(
        default_factory=dict, description="Parameter name -> unit string"
    )
    reference_index: int | None = Field(
        None, ge=0, description="Reference row index for REF() function"
    )


# Metrics calculation schemas


class MetricsChartSpec(BaseModel):
    """Chart specification for metrics calculation."""

    id: str
    title: str = ""
    x_column: str
    y_columns: list[str]
    chart_type: Literal["line", "scatter", "area"] = "line"
    area_spec: AreaSpecModel | None = None
    baseline_spec: BaselineSpecModel | None = None
    scope: ChartScopeModel | None = None


class CalculateMetricsRequest(BaseModel):
    """Request for backend metrics calculation."""

    data: list[dict[str, Any]] | None = Field(default=None, description="Processed data rows")
    run_id: str | None = Field(
        default=None, description="Optional processing run identifier to reuse processed data"
    )
    charts: list[MetricsChartSpec] = Field(
        ..., description="Chart specifications for which to calculate metrics"
    )

    @model_validator(mode="after")
    def validate_data_source(self) -> CalculateMetricsRequest:
        if not self.run_id and not self.data:
            raise ValueError("Either 'data' or 'run_id' must be provided")
        return self


class ChartMetrics(BaseModel):
    """Calculated metrics for a single chart."""

    chart_id: str
    y_column: str | None = None
    area_total: float | None = None
    area_positive: float | None = None
    area_negative: float | None = None
    area_by_region: dict[str, float] = Field(default_factory=dict)


class CalculateMetricsResponse(BaseModel):
    """Response with calculated metrics for all charts."""

    metrics: list[ChartMetrics]


# Generic error schema


class ErrorResponse(BaseModel):
    """Standard error response format."""

    detail: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Optional error code (e.g., 'INVALID_CSV_HEADER')")
    request_id: str | None = Field(None, description="Request correlation ID")
    errors: list[dict[str, Any]] | None = Field(
        None, description="Validation error details when available"
    )


# Response models for untyped endpoints


class HealthResponse(BaseModel):
    status: str
    version: str


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str | None = None
    raw_data: list[dict[str, Any]]
    parameters: dict[str, float]
    parameter_units: dict[str, str]
    units: dict[str, str]
    columns: list[str]
    dtypes: dict[str, str]


class DetectColumnsResponse(BaseModel):
    suggestions: dict[str, str]


class ProcessRunDataResponse(BaseModel):
    """Response for GET /processing/runs/{run_id}/data."""

    processed_data: list[dict[str, Any]]


class SavedConfigSummary(BaseModel):
    """Lightweight config listing entry (no payload)."""

    id: int
    name: str
    domain: str
    created_at: str
    updated_at: str


class SavedConfigDetail(SavedConfigSummary):
    """Full config entry including the stored JSON payload."""

    config_data: dict[str, Any]


class ConfigSaveResponse(BaseModel):
    status: str
    id: int


class StatusResponse(BaseModel):
    status: str
