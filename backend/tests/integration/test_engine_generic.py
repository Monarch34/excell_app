"""
Integration tests for the generic processing service.
Tests operations + formulas pipeline.
"""

import pandas as pd
import pytest
from src.core.formulas.engine import UserFormula
from src.services.processing_service import processing_service

# Generic test data setup
RAW_DATA = [
    {"Time": 0.0, "Load": 0.0, "Extension": 0.0},
    {"Time": 1.0, "Load": 100.0, "Extension": 0.1},
    {"Time": 2.0, "Load": 200.0, "Extension": 0.2},
    {"Time": 3.0, "Load": 300.0, "Extension": 0.3},
]


def test_process_with_operations_and_formulas():
    """Test processing with find_zero + slice + offset + formulas."""
    df = pd.DataFrame(RAW_DATA)

    operations = [
        {"type": "find_zero", "config": {"column": "Extension", "result_key": "extension"}},
        {"type": "slice_from_index", "config": {"index_key": "extension_zero_index"}},
        {
            "type": "offset_correction",
            "config": {
                "columns": [
                    {"source": "Load", "output": "Corrected Load"},
                    {"source": "Extension", "output": "Corrected Extension"},
                ],
                "abs_value": False,
            },
        },
    ]

    formulas = [
        UserFormula(name="DoubleLoad", formula="[Corrected Load] * 2", unit="N"),
    ]

    parameters = {"length": 50.0, "width": 10.0, "thickness": 2.0}

    processed_df, results = processing_service.process(
        df=df,
        operations=operations,
        formulas=formulas,
        parameters=parameters,
    )

    # Check operations ran
    assert "extension_zero_index" in results
    assert "extension_value" in results
    assert "Corrected Load" in processed_df.columns
    assert "Corrected Extension" in processed_df.columns

    # Check formula applied
    assert "DoubleLoad" in processed_df.columns


def test_process_with_column_mapping():
    """Test that column_mapping resolves role names to actual column names."""
    df = pd.DataFrame(RAW_DATA)

    operations = [
        {"type": "find_zero", "config": {"column": "ext", "result_key": "ext"}},
    ]

    column_mapping = {"ext": "Extension"}

    processed_df, results = processing_service.process(
        df=df,
        operations=operations,
        formulas=[],
        parameters={},
        column_mapping=column_mapping,
    )

    assert "ext_zero_index" in results


def test_process_formulas_only():
    """Test processing with formulas only (no operations)."""
    df = pd.DataFrame(RAW_DATA)

    formulas = [
        UserFormula(name="LoadPerTime", formula="[Load] / ([Time] + 1)", unit="N/s"),
    ]

    processed_df, results = processing_service.process(
        df=df,
        operations=[],
        formulas=formulas,
        parameters={},
    )

    assert "LoadPerTime" in processed_df.columns
    assert results == {}


def test_process_empty_operations_and_formulas():
    """Test processing with no operations or formulas."""
    df = pd.DataFrame(RAW_DATA)

    processed_df, results = processing_service.process(
        df=df,
        operations=[],
        formulas=[],
        parameters={},
    )

    assert len(processed_df) == len(RAW_DATA)
    assert results == {}


def test_process_parameters_available_in_formulas():
    """Test that user parameters are available in formulas."""
    df = pd.DataFrame(RAW_DATA)

    formulas = [
        UserFormula(name="Stress", formula="[Load] / [A0]", unit="MPa"),
    ]

    # A0 = width * thickness = 10 * 2 = 20
    parameters = {"A0": 20.0}

    processed_df, results = processing_service.process(
        df=df,
        operations=[],
        formulas=formulas,
        parameters=parameters,
    )

    assert "Stress" in processed_df.columns
    # Load=200 at row 2, A0=20 -> Stress=10
    assert processed_df.iloc[2]["Stress"] == pytest.approx(10.0)


def test_operation_results_available_in_formulas():
    """Test that operation results are merged into params for formulas."""
    df = pd.DataFrame(RAW_DATA)

    operations = [
        {"type": "find_zero", "config": {"column": "Extension", "result_key": "extension"}},
    ]

    formulas = [
        UserFormula(
            name="SlackTimesLoad",
            formula="[extension_value] * [Load]",
            unit="",
        ),
    ]

    processed_df, results = processing_service.process(
        df=df,
        operations=operations,
        formulas=formulas,
        parameters={},
    )

    # extension_value should be 0 (first zero found at index 0)
    assert "SlackTimesLoad" in processed_df.columns


def test_process_raises_when_derived_parameter_fails():
    """Derived parameter failures should fail fast for clearer debugging."""
    df = pd.DataFrame(RAW_DATA)

    with pytest.raises(ValueError, match="Failed to compute derived item 'A0'"):
        processing_service.process(
            df=df,
            operations=[],
            formulas=[],
            parameters={},
            derived_parameters=[{"name": "A0", "formula": "[Missing] * 2"}],
        )


def test_process_returns_scalar_derived_parameters_in_results():
    """Computed scalar derived parameters should be returned for frontend summary display."""
    df = pd.DataFrame(RAW_DATA)

    processed_df, results = processing_service.process(
        df=df,
        operations=[],
        formulas=[],
        parameters={"width": 10.0, "thickness": 2.0},
        derived_parameters=[{"name": "A0", "formula": "[width] * [thickness]"}],
    )

    assert len(processed_df) == len(RAW_DATA)
    assert "A0" in results
    assert results["A0"] == pytest.approx(20.0)
    # Original user parameters should not be echoed into results.
    assert "width" not in results
    assert "thickness" not in results
