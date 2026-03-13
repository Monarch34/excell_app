/**
 * Core domain types for the CSV Analysis application.
 * These types are framework-independent and represent the business domain.
 */

// ─── Dataset ───────────────────────────────────────────────────────────────────

export interface Dataset {
  filename: string;
  datasetId: string | null;
  columns: ColumnDef[];
  rows: Record<string, number | string | null>[];
  metadata: DatasetMetadata;
}

export interface DatasetMetadata {
  parameters: ParameterSet | null;
  parameterUnits: Record<string, string>;
  units: Record<string, string>;
  rowCount: number;
  parseWarnings: string[];
}

export interface ParameterSet {
  [key: string]: number;
}

export interface ColumnDef {
  name: string;
  type: 'numeric' | 'text';
  unit: string;
  selected: boolean;
}

// ─── Parameters ────────────────────────────────────────────────────────────────

export interface Parameter {
  name: string;
  value: number | null;
  unit: string;
}

// ─── Derived Columns ───────────────────────────────────────────────────────────

export interface DerivedColumnDef {
  id: string;
  name: string;
  formula: string;
  unit: string;
  description: string;
  dependencies: string[];
  enabled: boolean;
  type?: 'column' | 'parameter';
}

// ─── Charts ────────────────────────────────────────────────────────────────────

export type ChartType = 'line' | 'scatter' | 'area';
export type AreaMode = 'positive' | 'negative' | 'total';
export type BaselineAxis = 'x' | 'y';
export type BaselineRegion = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'all';

export interface ChartSpec {
  id: string;
  title: string;
  xColumn: string;
  yColumns: string[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  chartType: ChartType | null;
  baselineSpec?: BaselineSpec | null;
  areaSpec: AreaSpec | null;
  lineColor: string | null;
  fillColor: string | null;
  fillOpacity: number | null;
  lineWidth?: number | null;
  markerSize?: number | null;
  annotations?: {
    x: number;
    y: number;
    text: string;
    showArrow?: boolean;
  }[];
}

export interface AreaSpec {
  mode: AreaMode;
  baseline: number;
  baselineAxis?: BaselineAxis;
  xColumn: string;
  yColumn: string;
  label?: string | null;
}

export interface BaselineSpec {
  xBaseline: number;
  yBaseline: number;
  regions: BaselineRegion[];
}

// ─── Analysis ──────────────────────────────────────────────────────────────────

export interface AnalysisMetric {
  id: string;
  chartId: string;
  name: string;
  value: number;
  unit: string;
  computedAt: string;
}

// ─── Operations ────────────────────────────────────────────────────────────────

export interface OperationSpec {
  type: string;
  config: Record<string, unknown>;
}

// ─── Column Metadata (for export styling) ─────────────────────────────────────

export interface ColumnMeta {
  label: string;
  unit: string;
  color: string | null;
}

export interface MatchingColumnGroup {
  id: string;
  name: string;
  color: string;
  columns: string[];
}

// ─── Configuration ─────────────────────────────────────────────────────────────

export interface AnalysisConfig {
  version: string;
  name: string;
  description: string;
  selectedColumns: string[];
  parameters: Parameter[];
  derivedColumns: DerivedColumnDef[];
  charts: ChartSpec[];
  columnOrder: string[];
  parameterOrder: string[];
  separators: number[];
  separatorColor?: string;
  columnMetadata?: Record<string, ColumnMeta>;
  matchingGroups?: MatchingColumnGroup[];
  createdAt: string;
  updatedAt: string;
}

// ─── Formula Tokens ─────────────────────────────────────────────────────────

export type FormulaTokenType = 'reference' | 'operator';

export interface FormulaToken {
  type: FormulaTokenType;
  value: string;
  /** If true, the value is output as-is (e.g., REF([Column])) without additional brackets */
  raw?: boolean;
}

// ─── Report Export ─────────────────────────────────────────────────────────────

export interface ReportExportSpec {
  projectName: string;
  customFilename: string;
  includeDataSheet: boolean;
  includeCalculationsSheet: boolean;
  includeAnalysisSheet: boolean;
  includeChartsSheet: boolean;
}

// ─── Validation ────────────────────────────────────────────────────────────────

export interface ValidationError {
  code: string;
  message: string;
  field?: string;
  suggestions?: string[];
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

// ─── Chart UI State (not serialized to config) ────────────────────────────────

export interface ChartState {
  chartId: string;
  xRange: [number, number] | null;
  yRange: [number, number] | null;
  hiddenTraces: string[];
  isOpen?: boolean;
}
