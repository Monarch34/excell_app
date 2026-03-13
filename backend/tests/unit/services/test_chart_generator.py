"""
Unit tests for src/services/chart_generator.py

Tests chart generation with generate_from_spec.
"""

from io import BytesIO

import numpy as np
import pandas as pd
import pytest
from PIL import Image
from src.services.chart_generator import ChartGenerator


class TestChartGeneratorInit:
    """Tests for ChartGenerator initialization."""

    def test_creates_instance(self):
        """Should create ChartGenerator instance."""
        generator = ChartGenerator()
        assert generator is not None

    def test_has_figsize_attribute(self):
        """Should have figsize configuration."""
        generator = ChartGenerator()
        assert hasattr(generator, "figsize")
        assert isinstance(generator.figsize, tuple)

    def test_has_dpi_attribute(self):
        """Should have DPI configuration."""
        generator = ChartGenerator()
        assert hasattr(generator, "dpi")
        assert generator.dpi > 0


class TestGenerateFromSpec:
    """Tests for generate_from_spec method."""

    @pytest.fixture
    def generator(self):
        return ChartGenerator()

    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "Strain": [0.0, 0.01, 0.02, 0.03, 0.04],
                "Stress": [0.0, 10.0, 20.0, 30.0, 40.0],
                "Load": [0.0, 100.0, 200.0, 300.0, 400.0],
            }
        )

    def test_returns_bytesio_buffer(self, generator, sample_df):
        """Should return a BytesIO buffer."""
        spec = {
            "title": "Test Chart",
            "x_column": "Strain",
            "y_columns": ["Stress"],
            "chart_type": "line",
        }
        result = generator.generate_from_spec(sample_df, spec)
        assert isinstance(result, BytesIO)

    def test_buffer_contains_valid_png(self, generator, sample_df):
        """Buffer should contain valid PNG image data."""
        spec = {
            "title": "Test Chart",
            "x_column": "Strain",
            "y_columns": ["Stress"],
            "chart_type": "line",
        }
        result = generator.generate_from_spec(sample_df, spec)
        result.seek(0)
        img = Image.open(result)
        assert img.format == "PNG"

    def test_chart_has_expected_dimensions(self, generator, sample_df):
        """Chart should have reasonable dimensions."""
        spec = {
            "title": "Test Chart",
            "x_column": "Strain",
            "y_columns": ["Stress"],
            "chart_type": "line",
        }
        result = generator.generate_from_spec(sample_df, spec)
        result.seek(0)
        img = Image.open(result)
        assert img.width > 100
        assert img.height > 100
        assert img.width < 3000
        assert img.height < 3000

    def test_scatter_chart_type(self, generator, sample_df):
        """Should generate scatter chart."""
        spec = {
            "title": "Scatter Test",
            "x_column": "Strain",
            "y_columns": ["Stress"],
            "chart_type": "scatter",
        }
        result = generator.generate_from_spec(sample_df, spec)
        assert isinstance(result, BytesIO)

    def test_area_with_fill(self, generator, sample_df):
        """Should generate chart with area fill."""
        spec = {
            "title": "Area Test",
            "x_column": "Strain",
            "y_columns": ["Stress"],
            "chart_type": "line",
            "area_spec": {
                "mode": "positive",
                "baseline": 0,
                "x_column": "Strain",
                "y_column": "Stress",
            },
        }
        result = generator.generate_from_spec(sample_df, spec)
        assert isinstance(result, BytesIO)

    def test_multiple_y_columns(self, generator, sample_df):
        """Should handle multiple y columns."""
        spec = {
            "title": "Multi Y",
            "x_column": "Strain",
            "y_columns": ["Stress", "Load"],
            "chart_type": "line",
        }
        result = generator.generate_from_spec(sample_df, spec)
        assert isinstance(result, BytesIO)

    def test_missing_x_column_raises_error(self, generator, sample_df):
        """Should raise error for missing x column."""
        spec = {
            "title": "Bad Chart",
            "x_column": "NonExistent",
            "y_columns": ["Stress"],
            "chart_type": "line",
        }
        with pytest.raises(ValueError, match="not found"):
            generator.generate_from_spec(sample_df, spec)

    def test_handles_nan_values(self, generator):
        """Should handle NaN values gracefully."""
        df = pd.DataFrame(
            {
                "X": [0.0, 0.01, np.nan, 0.03, 0.04],
                "Y": [0.0, 10.0, np.nan, 30.0, 40.0],
            }
        )
        spec = {
            "title": "NaN Test",
            "x_column": "X",
            "y_columns": ["Y"],
            "chart_type": "line",
        }
        result = generator.generate_from_spec(df, spec)
        assert isinstance(result, BytesIO)
