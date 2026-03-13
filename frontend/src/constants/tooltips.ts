/**
 * Centralized tooltip text for consistent inline help across the application.
 */

export const TOOLTIPS = {
  // Parameters
  PARAMETER_NAME: 'Unique identifier for this parameter. Use underscores instead of spaces.',
  PARAMETER_VALUE: 'Numeric value used in calculations and formulas.',
  PARAMETER_UNIT: 'Optional unit of measurement (e.g., mm, MPa, %).',

  // Formulas
  FORMULA_SYNTAX:
    'Use [Column Name] to reference columns. Available functions: SUM, AVG, ABS, SQRT, MAX, MIN, REF (for reference row values).',
  FORMULA_REFERENCE: 'REF([Column]) gets the value from the reference row for calculations.',
  DERIVED_PARAMETER:
    'Parameters calculated from formulas. Available globally across all calculations.',
  DERIVED_COLUMN: 'Columns calculated from formulas. Creates new data columns in your dataset.',

  // Charts
  CHART_TYPE:
    'Line: connected data points. Scatter: discrete points. Area: filled region under the curve.',
  CHART_X_COLUMN: 'Horizontal axis data (typically independent variable).',
  CHART_Y_COLUMNS: 'Vertical axis data (dependent variable). Can plot multiple series.',
  CHART_BASELINE:
    'Reference point for area calculations. Use for highlighting regions above/below a threshold.',
  CHART_ANNOTATIONS: 'Click on chart to add labeled points of interest.',

  // Analysis
  REFERENCE_ROW:
    'Starting point for relative calculations using REF(). Usually the first data point.',
  AREA_CALCULATION:
    'Calculated using trapezoidal integration. Regions can be defined relative to baseline.',

  // Column Selection
  COLUMN_MAPPING:
    'Map imported columns to standard names for consistent analysis across different datasets.',

  // Export
  CONFIG_SAVE: 'Save all formulas, charts, and parameters for reuse with similar datasets.',
  CONFIG_LOAD: 'Load previously saved configuration to quickly set up analysis.',
} as const;

export type TooltipKey = keyof typeof TOOLTIPS;
