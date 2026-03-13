"""
Unit test specific fixtures.
Focus on isolated, fast tests with mocked dependencies.
"""

import pandas as pd
import pytest


@pytest.fixture
def zero_strain_series() -> pd.Series:
    """Series with exact zeros at the start."""
    return pd.Series([0.0, 0.0, 0.0, 0.001, 0.002, 0.003, 0.005])


@pytest.fixture
def no_zero_strain_series() -> pd.Series:
    """Series without exact zeros (for fallback testing)."""
    return pd.Series([0.0001, 0.00005, 0.0002, 0.001, 0.002, 0.003])


@pytest.fixture
def negative_strain_series() -> pd.Series:
    """Series with negative values (edge case)."""
    return pd.Series([-0.001, -0.0005, 0.0, 0.001, 0.002])


@pytest.fixture
def mock_chart_buffer():
    """Create a minimal valid PNG for chart placeholder."""
    from io import BytesIO

    from PIL import Image

    img = Image.new("RGB", (100, 100), color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
