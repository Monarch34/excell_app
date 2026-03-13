# Report Export DTO

This project now uses a single backend export contract (`ExportRequest`) as the source of truth for report generation.

## Goals

- Keep frontend and backend aligned with one explicit payload.
- Avoid duplicated business logic in the frontend.
- Ensure chart preview/export parity by reusing the same backend rules.
- Make exports reproducible and easier to debug.

## Current Contract Highlights

- `schema_version`: DTO version string (currently `1.0`).
- `raw_data`: data rows to process.
- `parameters`, `units`, `parameter_units`.
- `operations`, `derived_parameters`, `user_formulas`, `derived_columns`.
- `selected_columns`, `column_mapping`.
- `charts`: line/scatter/area chart definitions with baseline + style options.
- `column_layout`: order, separators, matching groups.
- `column_colors`: explicit per-column export color overrides.
- `header_mapping`, `reference_index`.

## Compilation Flow

`POST /api/v3/reports/xlsx` now orchestrates:

1. `ReportCompiler.compile(request)`:
   - Applies operations and formulas.
   - Builds export dataframe and metric specs.
   - Generates chart images for all requested chart types.
   - Produces normalized layout/colors for the XLSX builder.
2. `XlsxReportBuilder.build(...)`:
   - Renders Data / Calculations / Analysis / Charts sheets.

## Color Behavior

- Preferred source: `column_colors` map.
- Fallback: derive column colors from `column_layout.matching_groups`.
- Headers remain standardized; group colors apply to unit/data cells.
