"""
Unit tests for src/services/xlsx_report_builder.py
"""

from io import BytesIO

import pandas as pd
import pytest
from openpyxl import load_workbook
from src.services.xlsx_report_builder import (
    AnalysisMetricSpec,
    DerivedColumnSpec,
    ParameterSpec,
    XlsxReportBuilder,
)


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Time": [0.0, 0.1, 0.2, 0.3, 0.4],
            "Load": [0.0, 10.0, 20.0, 15.0, 5.0],
            "Extension": [0.0, 0.01, 0.02, 0.03, 0.04],
            "Stress": [0.0, 100.0, 200.0, 150.0, 50.0],
        }
    )


@pytest.fixture
def column_units():
    return {"Load": "N", "Extension": "mm", "Stress": "MPa"}


@pytest.fixture
def derived_columns():
    return [
        DerivedColumnSpec(
            name="Stress",
            formula="[Load] / ([width] * [thickness])",
            unit="MPa",
            description="Engineering stress",
            dependencies="Load, width, thickness",
            enabled=True,
        ),
    ]


@pytest.fixture
def metrics():
    return [
        AnalysisMetricSpec(
            chart_id="chart-001",
            chart_title="Stress-Strain",
            name="Max Stress",
            value=200.0,
            unit="MPa",
            x_column="Extension",
            y_column="Stress",
        ),
        AnalysisMetricSpec(
            chart_id="chart-001",
            chart_title="Stress-Strain",
            name="Total Area",
            value=5.5,
            unit="MJ/m^3",
            x_column="Extension",
            y_column="Stress",
        ),
    ]


@pytest.fixture
def parameters():
    return [
        ParameterSpec(name="length", value=50.0, unit="mm"),
        ParameterSpec(name="width", value=12.5, unit="mm"),
        ParameterSpec(name="thickness", value=2.0, unit="mm"),
    ]


class TestXlsxReportBuilder:
    """Tests for XlsxReportBuilder."""

    def test_builds_workbook_with_four_sheets(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Should create workbook with 4 sheets."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
            project_name="Test",
        )

        wb = load_workbook(output)
        assert len(wb.sheetnames) == 4
        assert wb.sheetnames == ["Data", "Calculations", "Analysis", "Charts"]

    def test_data_sheet_has_correct_headers(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Data sheet row 1 should have column headers."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Data"]

        headers = [ws.cell(row=1, column=i).value for i in range(1, 5)]
        assert headers == ["Time", "Load", "Extension", "Stress"]

    def test_data_sheet_has_units_row(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Data sheet row 2 should have units."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Data"]

        units = [ws.cell(row=2, column=i).value for i in range(1, 5)]
        assert units[1] == "N"
        assert units[2] == "mm"
        assert units[3] == "MPa"

    def test_data_sheet_has_correct_row_count(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Data should start at row 3 with 5 data rows."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Data"]

        # Row 3 should be first data row
        assert ws.cell(row=3, column=1).value == 0.0
        # Row 7 should be last data row
        assert ws.cell(row=7, column=2).value == 5.0

    def test_calculations_sheet_has_derived_columns(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Calculations sheet should list derived column definitions."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Calculations"]

        # Row 2 should have first derived column
        assert ws.cell(row=2, column=1).value == "Stress"
        assert ws.cell(row=2, column=2).value == "[Load] / ([width] * [thickness])"

    def test_analysis_sheet_has_metrics(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Analysis sheet should have metrics."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Analysis"]

        assert ws.cell(row=2, column=2).value == "Max Stress"
        assert ws.cell(row=2, column=3).value == 200.0

    def test_analysis_sheet_has_parameters(
        self, sample_df, column_units, derived_columns, metrics, parameters
    ):
        """Analysis sheet should have parameters section."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        wb = load_workbook(output)
        ws = wb["Analysis"]

        # Parameters section starts after metrics
        # Row 6 = "Parameters" title (metrics=2 rows + header + 2 blank)
        param_title_row = len(metrics) + 4
        assert ws.cell(row=param_title_row, column=1).value == "Parameters"

    def test_empty_data(self):
        """Should handle empty DataFrame."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=pd.DataFrame(),
            column_units={},
            derived_columns=[],
            metrics=[],
            parameters=[],
            chart_images=[],
        )

        wb = load_workbook(output)
        assert len(wb.sheetnames) == 4

    def test_returns_bytesio(self, sample_df, column_units, derived_columns, metrics, parameters):
        """Should return a BytesIO object."""
        builder = XlsxReportBuilder()
        output = builder.build(
            df=sample_df,
            column_units=column_units,
            derived_columns=derived_columns,
            metrics=metrics,
            parameters=parameters,
            chart_images=[],
        )

        assert isinstance(output, BytesIO)
        assert len(output.getvalue()) > 0
