"""
XLSX Report Builder - Creates 4-sheet workbooks per the redesigned spec.

Sheets:
1. Data - selected original columns + derived columns
2. Calculations - derived column definitions
3. Analysis - metrics and parameters
4. Charts - embedded PNG images from matplotlib
"""

import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XlImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from src.utils.helpers import normalize_hex_color as _normalize_fill_color
from src.utils.styling import (
    DATA_HEADER_FILL,
    DATA_HEADER_FONT,
    HEADER_FILL,
    HEADER_FONT,
    PARAM_HEADER_FILL,
    PARAM_UNIT_FILL,
    SEPARATOR_FILL,
    THIN_BORDER,
    TITLE_FONT,
    UNITS_FILL,
    UNITS_FONT,
)

logger = logging.getLogger(__name__)


@dataclass
class DerivedColumnSpec:
    """Spec for a derived column in the report."""

    name: str
    formula: str
    unit: str = ""
    description: str = ""
    dependencies: str = ""
    enabled: bool = True


@dataclass
class AnalysisMetricSpec:
    """Spec for an analysis metric in the report."""

    chart_id: str
    chart_title: str
    name: str
    value: float
    unit: str = ""
    x_column: str = ""
    y_column: str = ""


@dataclass
class ParameterSpec:
    """Spec for a parameter in the report."""

    name: str
    value: float
    unit: str = ""


class XlsxReportBuilder:
    """
    Builds a 4-sheet XLSX report per the redesigned specification.
    """

    def build(
        self,
        df: pd.DataFrame,
        column_units: dict[str, str],
        derived_columns: list[DerivedColumnSpec],
        metrics: list[AnalysisMetricSpec],
        parameters: list[ParameterSpec],
        chart_images: list[tuple],  # List of (title, BytesIO_png)
        project_name: str = "Report",
        column_layout: dict[str, Any] | None = None,
        column_colors: dict[str, str] | None = None,
        header_mapping: dict[str, str] | None = None,
    ) -> BytesIO:
        """
        Build the complete 4-sheet XLSX report.

        Args:
            df: DataFrame with all data (selected originals + derived)
            column_units: Mapping of column name -> unit string
            derived_columns: Derived column definitions
            metrics: Analysis metrics
            parameters: Parameters used
            chart_images: List of (title, BytesIO) for chart PNGs
            project_name: Name for the report
            column_layout: Optional dict with column_order, linked_groups, separator_indices
            column_colors: Optional dict of column name -> hex color string
            header_mapping: Optional dict of column key -> display label

        Returns:
            BytesIO containing the XLSX file
        """
        logger.info(f"Building XLSX report: {project_name}")

        # Apply column reordering if specified
        if column_layout and column_layout.get("column_order"):
            ordered_cols = [c for c in column_layout["column_order"] if c in df.columns]
            # Add any columns not in the order (derived columns added later, etc.)
            for c in df.columns:
                if c not in ordered_cols:
                    ordered_cols.append(c)
            df = df[ordered_cols]

        wb = Workbook()

        # Sheet 1: Data
        separator_indices = column_layout.get("separator_indices", []) if column_layout else []
        separator_color = column_layout.get("separator_color") if column_layout else None
        self._build_data_sheet(
            wb,
            df,
            column_units,
            parameters,
            separator_indices,
            separator_color,
            column_colors or {},
            header_mapping or {},
        )

        # Sheet 2: Calculations
        self._build_calculations_sheet(wb, derived_columns)

        # Sheet 3: Analysis
        self._build_analysis_sheet(wb, metrics, parameters)

        # Sheet 4: Charts
        self._build_charts_sheet(wb, chart_images)

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        logger.info("XLSX report built successfully")
        return output

    def _build_data_sheet(
        self,
        wb: Workbook,
        df: pd.DataFrame,
        column_units: dict[str, str],
        parameters: list[ParameterSpec],
        separator_indices: list[int],
        separator_color: str | None,
        column_colors: dict[str, str],
        header_mapping: dict[str, str],
    ) -> None:
        """Sheet 1: Data - headers, units, data rows, separators, parameter metadata."""
        ws = wb.active
        ws.title = "Data"
        normalized_separator = _normalize_fill_color(separator_color)
        separator_fill = (
            PatternFill(
                start_color=normalized_separator, end_color=normalized_separator, fill_type="solid"
            )
            if normalized_separator
            else SEPARATOR_FILL
        )

        columns = list(df.columns)
        column_group_fills: dict[str, PatternFill] = {}
        for col_name in columns:
            normalized = _normalize_fill_color(column_colors.get(col_name))
            if normalized:
                column_group_fills[col_name] = PatternFill(
                    start_color=normalized,
                    end_color=normalized,
                    fill_type="solid",
                )

        # Build column list with separator columns inserted
        write_columns: list[str | None] = []  # None = separator column
        sorted_seps = sorted(set(separator_indices))
        sep_set = set(sorted_seps)

        for i, col_name in enumerate(columns):
            write_columns.append(col_name)
            if i in sep_set:
                write_columns.append(None)  # separator

        num_write_cols = len(write_columns)

        # Row 1: Headers
        for col_idx, col_name in enumerate(write_columns, 1):
            if col_name is None:
                # Separator column
                cell = ws.cell(row=1, column=col_idx, value="")
                cell.fill = separator_fill
                cell.border = THIN_BORDER
            else:
                display_name = header_mapping.get(col_name, col_name)
                cell = ws.cell(row=1, column=col_idx, value=display_name)
                cell.font = DATA_HEADER_FONT
                cell.fill = DATA_HEADER_FILL
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="center")

        # Row 2: Units
        for col_idx, col_name in enumerate(write_columns, 1):
            if col_name is None:
                cell = ws.cell(row=2, column=col_idx, value="")
                cell.fill = separator_fill
                cell.border = THIN_BORDER
            else:
                unit = column_units.get(col_name, "")

                cell = ws.cell(row=2, column=col_idx, value=unit)
                cell.font = UNITS_FONT
                cell.fill = column_group_fills.get(col_name, UNITS_FILL)
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="center")

        # Row 3+: Data
        for row_idx, (_, row) in enumerate(df.iterrows(), 3):
            for col_idx, col_name in enumerate(write_columns, 1):
                if col_name is None:
                    # Separator column - green fill, empty
                    cell = ws.cell(row=row_idx, column=col_idx, value="")
                    cell.fill = separator_fill
                else:
                    value = row[col_name]
                    if pd.isna(value):
                        cell = ws.cell(row=row_idx, column=col_idx, value="")
                    elif isinstance(value, int | np.integer):
                        cell = ws.cell(row=row_idx, column=col_idx, value=int(value))
                        cell.number_format = "0"
                    elif isinstance(value, float | np.floating):
                        float_val = float(value)
                        if not np.isfinite(float_val):
                            cell = ws.cell(row=row_idx, column=col_idx, value="")
                        else:
                            cell = ws.cell(row=row_idx, column=col_idx, value=float_val)
                            cell.number_format = "0.000000"
                    else:
                        cell = ws.cell(row=row_idx, column=col_idx, value=str(value))

                    group_fill = column_group_fills.get(col_name)
                    if group_fill:
                        cell.fill = group_fill

        # Auto-width columns
        for col_idx, col_name in enumerate(write_columns, 1):
            col_letter = get_column_letter(col_idx)
            if col_name is None:
                ws.column_dimensions[col_letter].width = 3  # Narrow separator
            else:
                ws.column_dimensions[col_letter].width = max(12, len(col_name) + 4)

        # Parameter metadata area: 2 columns gap after data, then vertical block
        if parameters:
            param_start_col = num_write_cols + 3  # 2-column gap

            # Row 1: Parameter names (bold, gray bg)
            for p_idx, p in enumerate(parameters):
                col = param_start_col + p_idx
                cell = ws.cell(row=1, column=col, value=p.name)
                cell.font = HEADER_FONT
                cell.fill = PARAM_HEADER_FILL
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="center")

            # Row 2: Units (italic, light gray)
            for p_idx, p in enumerate(parameters):
                col = param_start_col + p_idx
                cell = ws.cell(row=2, column=col, value=p.unit)
                cell.font = UNITS_FONT
                cell.fill = PARAM_UNIT_FILL
                cell.border = THIN_BORDER
                cell.alignment = Alignment(horizontal="center")

            # Row 3: Values
            for p_idx, p in enumerate(parameters):
                col = param_start_col + p_idx
                if isinstance(p.value, float | np.floating) and not np.isfinite(float(p.value)):
                    cell = ws.cell(row=3, column=col, value="")
                else:
                    cell = ws.cell(row=3, column=col, value=p.value)
                    if isinstance(p.value, float):
                        cell.number_format = "0.000000"
                cell.border = THIN_BORDER

            # Set widths for parameter columns
            for p_idx, p in enumerate(parameters):
                col_letter = get_column_letter(param_start_col + p_idx)
                ws.column_dimensions[col_letter].width = max(12, len(p.name) + 4)

        logger.debug(
            f"Data sheet: {len(df)} rows x {len(columns)} columns "
            f"({len(separator_indices)} separators, {len(parameters)} params)"
        )

    def _build_calculations_sheet(
        self,
        wb: Workbook,
        derived_columns: list[DerivedColumnSpec],
    ) -> None:
        """Sheet 2: Calculations - derived column definitions."""
        ws = wb.create_sheet("Calculations")

        headers = ["Name", "Formula", "Unit", "Description", "Referenced Columns", "Status"]

        # Header row
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.border = THIN_BORDER
            cell.alignment = Alignment(horizontal="center")

        # Data rows
        for row_idx, dc in enumerate(derived_columns, 2):
            ws.cell(row=row_idx, column=1, value=dc.name).border = THIN_BORDER
            ws.cell(row=row_idx, column=2, value=dc.formula).border = THIN_BORDER
            ws.cell(row=row_idx, column=3, value=dc.unit).border = THIN_BORDER
            ws.cell(row=row_idx, column=4, value=dc.description).border = THIN_BORDER
            ws.cell(row=row_idx, column=5, value=dc.dependencies).border = THIN_BORDER
            status = "Active" if dc.enabled else "Disabled"
            ws.cell(row=row_idx, column=6, value=status).border = THIN_BORDER

        # Column widths
        widths = [20, 50, 10, 30, 30, 10]
        for col_idx, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        logger.debug(f"Calculations sheet: {len(derived_columns)} derived columns")

    def _build_analysis_sheet(
        self,
        wb: Workbook,
        metrics: list[AnalysisMetricSpec],
        parameters: list[ParameterSpec],
    ) -> None:
        """Sheet 3: Analysis - metrics and parameters."""
        ws = wb.create_sheet("Analysis")

        # Metrics section
        metric_headers = ["Chart Title", "Metric Name", "Value", "Unit", "X Column", "Y Column"]
        for col_idx, header in enumerate(metric_headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.border = THIN_BORDER

        for row_idx, m in enumerate(metrics, 2):
            ws.cell(row=row_idx, column=1, value=m.chart_title).border = THIN_BORDER
            ws.cell(row=row_idx, column=2, value=m.name).border = THIN_BORDER

            if isinstance(m.value, float | np.floating) and not np.isfinite(float(m.value)):
                cell = ws.cell(row=row_idx, column=3, value="")
            else:
                cell = ws.cell(row=row_idx, column=3, value=m.value)
                if isinstance(m.value, float):
                    cell.number_format = "0.000000"
            cell.border = THIN_BORDER
            ws.cell(row=row_idx, column=4, value=m.unit).border = THIN_BORDER
            ws.cell(row=row_idx, column=5, value=m.x_column).border = THIN_BORDER
            ws.cell(row=row_idx, column=6, value=m.y_column).border = THIN_BORDER

        # Parameters section
        param_start_row = len(metrics) + 4
        ws.cell(row=param_start_row, column=1, value="Parameters").font = Font(bold=True, size=12)

        param_headers = ["Name", "Value", "Unit"]
        for col_idx, header in enumerate(param_headers, 1):
            cell = ws.cell(row=param_start_row + 1, column=col_idx, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.border = THIN_BORDER

        for row_idx, p in enumerate(parameters, param_start_row + 2):
            ws.cell(row=row_idx, column=1, value=p.name).border = THIN_BORDER
            if isinstance(p.value, float | np.floating) and not np.isfinite(float(p.value)):
                cell = ws.cell(row=row_idx, column=2, value="")
            else:
                cell = ws.cell(row=row_idx, column=2, value=p.value)
                if isinstance(p.value, float):
                    cell.number_format = "0.000000"
            cell.border = THIN_BORDER
            ws.cell(row=row_idx, column=3, value=p.unit).border = THIN_BORDER

        # Column widths
        widths = [20, 20, 15, 10, 20, 20]
        for col_idx, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = w

        logger.debug(f"Analysis sheet: {len(metrics)} metrics, {len(parameters)} parameters")

    def _build_charts_sheet(
        self,
        wb: Workbook,
        chart_images: list[tuple],
    ) -> None:
        """Sheet 4: Charts - embedded PNG images."""
        ws = wb.create_sheet("Charts")

        IMAGE_WIDTH = 800
        IMAGE_HEIGHT = 500
        ROWS_PER_CHART = 36
        current_row = 1

        for chart_title, chart_buf in chart_images:
            try:
                # Title
                cell = ws.cell(row=current_row, column=1, value=chart_title)
                cell.font = TITLE_FONT
                ws.row_dimensions[current_row].height = 22

                # Image
                chart_buf.seek(0)
                img = XlImage(chart_buf)
                img.width = IMAGE_WIDTH
                img.height = IMAGE_HEIGHT

                anchor = f"A{current_row + 1}"
                ws.add_image(img, anchor)

                current_row += ROWS_PER_CHART

            except Exception as e:
                logger.warning(f"Chart '{chart_title}' failed: {e}")
                ws.cell(
                    row=current_row + 1,
                    column=1,
                    value=f"Chart could not be generated: {e}",
                )
                current_row += 3

        ws.column_dimensions["A"].width = 120
        logger.debug(f"Charts sheet: {len(chart_images)} charts embedded")
