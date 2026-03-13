"""
Root conftest.py - Shared fixtures for all tests.
"""

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for tests

from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.services.csv_parser import CSVParser

# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def sample_data_path(project_root) -> Path:
    """Path to test data directory."""
    return project_root / "tests" / "data"


@pytest.fixture(scope="session")
def real_csv_path(sample_data_path) -> Path:
    """Path to the actual sample CSV file."""
    return sample_data_path / "sample.csv"


@pytest.fixture(scope="session")
def snapshots_path(project_root) -> Path:
    """Path to snapshots directory."""
    return project_root / "tests" / "snapshots"


# ============================================================================
# Data Fixtures (Session-scoped for performance)
# ============================================================================


@pytest.fixture(scope="session")
def real_parsed_data(real_csv_path):
    """
    Parse the actual sample CSV file once per session.
    Returns tuple: (DataFrame, parameters_dict, units_dict, parameter_units_dict)
    """
    df, parameters, units, parameter_units = CSVParser.parse(str(real_csv_path))
    return df, parameters, units, parameter_units


@pytest.fixture
def sample_dataframe(real_parsed_data) -> pd.DataFrame:
    """Get a copy of the sample DataFrame for tests that modify it."""
    df, _, _, _ = real_parsed_data
    return df.copy()


@pytest.fixture
def sample_parameters(real_parsed_data) -> dict:
    """Get the sample parameters as a dict."""
    _, parameters, _, _ = real_parsed_data
    return parameters


@pytest.fixture
def sample_units(real_parsed_data) -> dict:
    """Get the sample units dictionary."""
    _, _, units, _ = real_parsed_data
    return units


@pytest.fixture
def sample_parameter_units(real_parsed_data) -> dict:
    """Get the sample parameter units dictionary."""
    _, _, _, parameter_units = real_parsed_data
    return parameter_units


# ============================================================================
# Synthetic Data Factories
# ============================================================================


@pytest.fixture
def make_synthetic_dataframe():
    """
    Factory fixture for creating synthetic test DataFrames.
    Useful for edge case testing.
    """

    def _factory(
        n_rows: int = 100, include_zeros: bool = True, include_nans: bool = False
    ) -> pd.DataFrame:
        np.random.seed(42)  # Reproducible

        time = np.linspace(0, 10, n_rows)
        extension = np.linspace(-0.0001, 0.5, n_rows)
        load = np.linspace(-0.001, 1.0, n_rows)

        if include_zeros:
            strain = np.concatenate([np.zeros(5), np.linspace(0.001, 0.1, n_rows - 5)])
        else:
            strain = np.linspace(0.001, 0.1, n_rows)

        stress = strain * 100

        df = pd.DataFrame(
            {
                "Time": time,
                "Extension": extension,
                "Load": load,
                "Tensile strain": strain,
                "Tensile stress": stress,
                "Tensile extension": extension,
            }
        )

        if include_nans:
            df.iloc[-5:, 3:] = np.nan

        return df

    return _factory


# ============================================================================
# CSV Content Fixtures
# ============================================================================


@pytest.fixture
def csv_content_valid() -> str:
    """Valid CSV content string matching expected format."""
    return """Dimension : Length,50,mm
Dimension : Width,20,mm
Dimension : Thickness,0.04470,mm

Time,Extension,Load,Tensile strain,Tensile stress,Tensile extension
(sec),(mm),(N),(mm/mm),(MPa),(mm)
0.00000,-0.00016,-0.00350,-0.00003,-0.039,-0.00016
0.05000,-0.00016,-0.00225,-0.00003,-0.025,-0.00016
0.10000,0.00047,-0.00294,0.00009,-0.033,0.00047
0.15000,0.00062,-0.00263,0.00012,-0.029,0.00062
0.20000,0.00203,-0.00255,0.00041,-0.028,0.00203
"""


@pytest.fixture
def csv_buffer_valid(csv_content_valid) -> BytesIO:
    """BytesIO buffer with valid CSV content."""
    return BytesIO(csv_content_valid.encode("utf-8"))


# ============================================================================
# Service Fixtures
# ============================================================================


@pytest.fixture
def chart_generator():
    """ChartGenerator instance."""
    from src.services.chart_generator import ChartGenerator

    return ChartGenerator()
