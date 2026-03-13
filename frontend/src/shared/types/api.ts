/**
 * API wire types.
 *
 * Core contract types are sourced from generated OpenAPI schemas.
 * Keep this file as a compatibility layer for frontend-specific aliases.
 */

import type {
  AnalysisMetricModel,
  AnnotationModel,
  AreaSpecModel,
  BaselineSpecModel,
  CalculateMetricsResponse as CalculateMetricsResponseModel,
  ChartMetrics as ChartMetricsModel,
  ChartSpecModel,
  ColumnLayoutSpec,
  DerivedColumnModel,
  DerivedParameterDef,
  FormulaPreviewResponse as FormulaPreviewResponseModel,
  MatchingGroupSpecModel,
  MetricsChartSpec as MetricsChartSpecModel,
  OperationSpec,
  ProcessResponse as ProcessResponseModel,
  UserFormulaModel,
} from "./generated/openapi";

// Upload is custom at endpoint level (not defined as a shared backend schema).
export interface UploadResponse {
  dataset_id: string;
  filename: string;
  raw_data: Record<string, unknown>[];
  columns: string[];
  dtypes: Record<string, string>;
  parameters: Record<string, number> | null;
  parameter_units?: Record<string, string>;
  units: Record<string, string>;
}

export interface DetectColumnsResponse {
  [key: string]: string;
}

export type OperationSpecPayload = OperationSpec;
export type UserFormulaPayload = UserFormulaModel;
export type ProcessRow = Record<string, number | string | null>;
export type ProcessResultValue = number | string | boolean | null;
export type ProcessResults = Record<string, ProcessResultValue>;

export interface ProcessRequest {
  dataset_id: string;
  parameters?: Record<string, number>;
  units?: Record<string, string>;
  column_mapping?: Record<string, string>;
  project_name?: string;
  operations?: OperationSpecPayload[];
  user_formulas?: UserFormulaPayload[];
  derived_parameters?: DerivedParameterDef[];
  header_mapping?: Record<string, string>;
  initial_results?: ProcessResults;
}

export interface ProcessResponse extends Omit<ProcessResponseModel, "processed_data" | "results"> {
  processed_data?: ProcessRow[] | null;
  results: ProcessResults;
  run_id: string;
}

export interface ProcessRunDataResponse {
  processed_data: ProcessRow[];
}
export interface FormulaValidateRequest {
  formula: string;
  available_columns?: string[];
  available_parameters?: string[];
}

export interface FormulaValidateResponse {
  valid: boolean;
  errors: string[];
  referenced_columns: string[];
}

export interface FormulaPreviewRequest {
  dataset_id: string;
  formula: string;
  target_type?: "column" | "parameter";
  sample_start?: number;
  sample_size?: number;
  reference_index?: number | null;
  parameters?: Record<string, number>;
  column_mapping?: Record<string, string> | null;
  header_mapping?: Record<string, string>;
  user_formulas?: UserFormulaPayload[];
  derived_parameters?: DerivedParameterDef[];
}
export type FormulaPreviewErrorCode = "division" | "variable" | "syntax" | "dataset_expired" | "generic";

export interface FormulaPreviewResponse
  extends Omit<FormulaPreviewResponseModel, "values" | "is_scalar" | "error" | "error_code"> {
  values: number[];
  is_scalar: boolean;
  error: string | null;
  errorCode?: FormulaPreviewErrorCode;
}

export type DerivedColumnPayload = DerivedColumnModel;
export type AnnotationPayload = AnnotationModel;
export interface AreaSpecPayload extends AreaSpecModel {
  mode: "positive" | "negative" | "total";
  baseline: number;
  x_column: string;
  y_column: string;
  baseline_axis?: "x" | "y";
}
export type AnalysisMetricPayload = AnalysisMetricModel;
export type MatchingGroupPayload = MatchingGroupSpecModel;
export type ColumnLayoutPayload = ColumnLayoutSpec;
export type BaselineSpecPayload = BaselineSpecModel;
export type ParameterPayload = { name: string; value: number; unit: string };

export type ChartType = "line" | "scatter" | "area";

export interface ChartSpecPayload extends Omit<ChartSpecModel, "chart_type"> {
  chart_type: ChartType;
  area_spec?: AreaSpecPayload | null;
}

export interface MetricsChartSpec extends Omit<MetricsChartSpecModel, "chart_type"> {
  chart_type: ChartType;
  area_spec?: AreaSpecPayload | null;
}

export interface ExportRequest {
  dataset_id: string;
  schema_version?: string;
  units?: Record<string, string>;
  parameters?: Record<string, number>;
  project_name?: string;
  custom_filename?: string;
  selected_columns?: string[];
  column_mapping?: Record<string, string>;
  operations?: OperationSpecPayload[];
  derived_parameters?: DerivedParameterDef[];
  derived_columns?: DerivedColumnPayload[];
  charts?: ChartSpecPayload[];
  metrics?: AnalysisMetricPayload[];
  column_layout?: ColumnLayoutPayload;
  column_colors?: Record<string, string>;
  parameter_units?: Record<string, string>;
  header_mapping?: Record<string, string>;
  reference_index?: number | null;
}

export interface CalculateMetricsRequest {
  data?: ProcessRow[];
  run_id?: string;
  charts: MetricsChartSpec[];
}

export interface ChartMetrics extends Omit<ChartMetricsModel, "area_total" | "area_positive" | "area_negative" | "area_by_region"> {
  area_total: number | null;
  area_positive: number | null;
  area_negative: number | null;
  area_by_region: Record<string, number>;
}

export interface CalculateMetricsResponse extends Omit<CalculateMetricsResponseModel, "metrics"> {
  metrics: ChartMetrics[];
}

export interface HealthResponse {
  status: string;
}

export interface ApiError {
  detail: string;
  code?: string;
  request_id?: string;
}
