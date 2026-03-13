"""
Unit tests for src.api.serialization
"""

import math

import numpy as np
import pandas as pd
from src.api.serialization import dataframe_to_json_records, to_json_safe_value


def _is_json_null(v) -> bool:
    """True if a value would serialize as JSON null (Python None or NaN)."""
    if v is None:
        return True
    try:
        return math.isnan(v)
    except TypeError:
        return False


class TestDataframeToJsonRecords:
    def test_inf_replaced_with_none(self):
        df = pd.DataFrame({"a": [1.0, float("inf"), float("-inf")]})
        records = dataframe_to_json_records(df)
        assert records[1]["a"] is None
        assert records[2]["a"] is None

    def test_nan_replaced_with_none(self):
        df = pd.DataFrame({"a": [1.0, float("nan"), 3.0]})
        records = dataframe_to_json_records(df)
        assert records[1]["a"] is None

    def test_finite_values_preserved(self):
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        records = dataframe_to_json_records(df)
        assert records == [{"x": 1.0}, {"x": 2.0}, {"x": 3.0}]

    def test_original_dataframe_not_mutated(self):
        """dataframe_to_json_records must not modify the caller's DataFrame."""
        df = pd.DataFrame({"a": [float("inf"), 1.0]})
        original_values = df["a"].tolist()
        dataframe_to_json_records(df)
        assert df["a"].tolist() == original_values  # inf still present in original


class TestToJsonSafeValue:
    def test_none_passthrough(self):
        assert to_json_safe_value(None) is None

    def test_int_passthrough(self):
        assert to_json_safe_value(42) == 42

    def test_string_passthrough(self):
        assert to_json_safe_value("hello") == "hello"

    def test_nan_returns_none(self):
        assert to_json_safe_value(float("nan")) is None

    def test_inf_returns_none(self):
        assert to_json_safe_value(float("inf")) is None

    def test_neg_inf_returns_none(self):
        assert to_json_safe_value(float("-inf")) is None

    def test_numpy_int64_to_int(self):
        result = to_json_safe_value(np.int64(42))
        assert result == 42
        assert isinstance(result, int)

    def test_numpy_float32_to_float(self):
        result = to_json_safe_value(np.float32(3.14))
        assert isinstance(result, float)
        assert math.isclose(result, 3.14, rel_tol=1e-4)

    def test_pandas_na_returns_none(self):
        assert to_json_safe_value(pd.NA) is None

    def test_list_values_sanitized(self):
        result = to_json_safe_value([np.int64(1), float("nan"), 3.0])
        assert result == [1, None, 3.0]

    def test_dict_values_sanitized(self):
        result = to_json_safe_value({"a": np.int64(7), "b": float("inf")})
        assert result == {"a": 7, "b": None}
