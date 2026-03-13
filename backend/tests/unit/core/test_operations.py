"""
Unit tests for src/core/operations.py — Generic data operations.
"""

import numpy as np
import pandas as pd
import pytest
from src.core.operations import execute_operation, find_zero, offset_correction, slice_from_index


class TestFindZero:
    """Tests for find_zero operation."""

    def test_finds_exact_zero(self):
        df = pd.DataFrame({"Extension": [0.1, 0.0, 0.0, 0.5, 1.0]})
        _, results = find_zero(df, {"column": "Extension", "result_key": "ext"}, {})

        assert results["ext_zero_index"] == 2  # Last zero
        assert results["ext_value"] == 0.0

    def test_finds_near_zero_when_no_exact(self):
        df = pd.DataFrame({"Extension": [0.01, -0.001, 0.005, 0.5, 1.0]})
        _, results = find_zero(df, {"column": "Extension", "result_key": "ext"}, {})

        assert results["ext_zero_index"] == 1  # min abs
        assert results["ext_value"] == pytest.approx(-0.001)

    def test_raises_for_missing_column(self):
        df = pd.DataFrame({"Load": [1, 2, 3]})
        with pytest.raises(ValueError, match="not found"):
            find_zero(df, {"column": "Extension"}, {})

    def test_custom_search_percent(self):
        # All zeros in first 10%, only search there
        data = list(np.zeros(10)) + list(np.linspace(0.1, 1.0, 90))
        df = pd.DataFrame({"Col": data})
        _, results = find_zero(
            df, {"column": "Col", "search_percent": 0.05, "result_key": "col"}, {}
        )

        assert results["col_zero_index"] == 9  # Last zero in first 10 rows


class TestSliceFromIndex:
    """Tests for slice_from_index operation."""

    def test_slices_from_stored_index(self):
        df = pd.DataFrame({"A": [10, 20, 30, 40, 50]})
        results = {"start_idx": 2}
        sliced_df, _ = slice_from_index(df, {"index_key": "start_idx"}, results)

        assert len(sliced_df) == 3
        assert sliced_df["A"].iloc[0] == 30
        assert sliced_df.index[0] == 0  # Reset index

    def test_raises_for_missing_key(self):
        df = pd.DataFrame({"A": [1, 2, 3]})
        with pytest.raises(ValueError, match="not found"):
            slice_from_index(df, {"index_key": "nonexistent"}, {})


class TestOffsetCorrection:
    """Tests for offset_correction operation."""

    def test_corrects_single_column(self):
        df = pd.DataFrame({"Load": [10.0, 20.0, 30.0, 40.0]})
        config = {
            "columns": [{"source": "Load", "output": "Corrected Load"}],
        }
        corrected_df, results = offset_correction(df, config, {})

        assert "Corrected Load" in corrected_df.columns
        assert corrected_df["Corrected Load"].iloc[0] == 0.0
        assert corrected_df["Corrected Load"].iloc[1] == 10.0
        assert results["reference_Load"] == 10.0

    def test_corrects_multiple_columns(self):
        df = pd.DataFrame(
            {
                "Load": [5.0, 15.0, 25.0],
                "Ext": [0.1, 0.3, 0.5],
            }
        )
        config = {
            "columns": [
                {"source": "Load", "output": "CLoad"},
                {"source": "Ext", "output": "CExt"},
            ],
        }
        corrected_df, results = offset_correction(df, config, {})

        assert corrected_df["CLoad"].iloc[0] == 0.0
        assert corrected_df["CExt"].iloc[0] == 0.0
        assert results["reference_Load"] == 5.0
        assert results["reference_Ext"] == pytest.approx(0.1)

    def test_abs_value_option(self):
        df = pd.DataFrame({"Load": [10.0, 5.0, 15.0]})
        config = {
            "columns": [{"source": "Load", "output": "CLoad"}],
            "abs_value": True,
        }
        corrected_df, _ = offset_correction(df, config, {})

        # 5 - 10 = -5, abs = 5
        assert corrected_df["CLoad"].iloc[1] == 5.0

    def test_raises_for_missing_column(self):
        df = pd.DataFrame({"A": [1, 2, 3]})
        config = {"columns": [{"source": "B", "output": "CB"}]}
        with pytest.raises(ValueError, match="not found"):
            offset_correction(df, config, {})


class TestExecuteOperation:
    """Tests for the operation dispatcher."""

    def test_dispatches_find_zero(self):
        df = pd.DataFrame({"X": [0, 0, 1, 2]})
        _, results = execute_operation("find_zero", df, {"column": "X", "result_key": "x"}, {})
        assert "x_zero_index" in results

    def test_raises_for_unknown_operation(self):
        df = pd.DataFrame({"X": [1]})
        with pytest.raises(ValueError, match="Unknown operation"):
            execute_operation("nonexistent_op", df, {}, {})
