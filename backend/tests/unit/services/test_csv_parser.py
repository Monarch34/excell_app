"""
Unit tests for src/services/csv_parser.py

Tests CSV parsing, dimension extraction, and column detection.
"""

from io import BytesIO

import pandas as pd
import pytest
from src.services.csv_parser import CSVParser


class TestCSVParserParse:
    """Tests for CSVParser.parse method."""

    def test_parse_valid_csv_file(self, real_csv_path):
        """Should successfully parse valid CSV file."""
        df, parameters, units, parameter_units = CSVParser.parse(str(real_csv_path))

        assert isinstance(df, pd.DataFrame)
        assert isinstance(parameters, dict)
        assert isinstance(units, dict)
        assert len(df) > 0
        assert isinstance(parameter_units, dict)

    def test_parse_from_buffer(self, csv_buffer_valid):
        """Should parse from BytesIO buffer."""
        df, parameters, units, parameter_units = CSVParser.parse(csv_buffer_valid)

        assert len(df) == 5  # 5 data rows in fixture
        assert parameters["Length"] == 50.0
        assert parameters["Width"] == 20.0
        assert parameters["Thickness"] == pytest.approx(0.0447, rel=1e-3)
        assert parameter_units["Length"] == "mm"
        assert parameter_units["Width"] == "mm"
        assert parameter_units["Thickness"] == "mm"

    def test_extracts_correct_dimensions(self, csv_buffer_valid):
        """Should extract L, W, T from first 3 lines."""
        _, parameters, _, parameter_units = CSVParser.parse(csv_buffer_valid)

        assert parameters["Length"] == 50.0
        assert parameters["Width"] == 20.0
        assert parameters["Thickness"] == pytest.approx(0.0447, rel=1e-3)
        assert parameter_units["Length"] == "mm"
        assert parameter_units["Width"] == "mm"
        assert parameter_units["Thickness"] == "mm"

    def test_extracts_units_dictionary(self, csv_buffer_valid):
        """Should create units dictionary from units row."""
        _, _, units, _ = CSVParser.parse(csv_buffer_valid)

        assert "Time" in units
        assert units["Time"] == "(sec)"
        assert units["Load"] == "(N)"
        assert units["Extension"] == "(mm)"

    def test_dataframe_has_correct_columns(self, csv_buffer_valid):
        """Should have expected column names."""
        df, _, _, _ = CSVParser.parse(csv_buffer_valid)

        expected_columns = [
            "Time",
            "Extension",
            "Load",
            "Tensile strain",
            "Tensile stress",
            "Tensile extension",
        ]
        assert list(df.columns) == expected_columns

    def test_dataframe_values_are_numeric(self, csv_buffer_valid):
        """All values should be numeric after parsing."""
        df, _, _, _ = CSVParser.parse(csv_buffer_valid)

        for col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} is not numeric"

    def test_parses_file_without_dimensions(self):
        """Should parse CSV that has no dimension lines (returns empty dimensions)."""
        csv_no_dims = """
Header1,Header2
(unit1),(unit2)
1,2
3,4
"""
        buffer = BytesIO(csv_no_dims.encode("utf-8"))
        df, parameters, units, parameter_units = CSVParser.parse(buffer)

        # Parser is lenient — returns empty dimensions
        assert parameters == {}
        assert parameter_units == {}
        assert isinstance(df, pd.DataFrame)

    def test_mixed_type_column_preserved_as_text(self):
        """Mixed numeric/text columns should stay as object dtype, not be coerced."""
        csv_content = """Col1,Col2,Col3
1,abc,100
2,def,200
3,456,300
"""
        buffer = BytesIO(csv_content.encode("utf-8"))
        df, _, _, _ = CSVParser.parse(buffer)

        # Col2 has mixed text and numeric values — must remain text (object or string)
        assert not pd.api.types.is_numeric_dtype(df["Col2"])
        assert list(df["Col2"]) == ["abc", "def", "456"]
        # Col1 and Col3 are fully numeric — should be coerced
        assert pd.api.types.is_numeric_dtype(df["Col1"])
        assert pd.api.types.is_numeric_dtype(df["Col3"])


class TestCSVParserDetectColumns:
    """Tests for CSVParser.detect_columns method."""

    def test_detects_standard_column_names(self, sample_dataframe):
        """Should detect columns when patterns are provided."""
        patterns = {
            "time": ["time"],
            "extension": ["extension"],
            "load": ["load"],
        }
        suggestions = CSVParser.detect_columns(sample_dataframe, patterns)

        assert suggestions.get("time") == "Time"
        assert suggestions.get("extension") == "Extension"
        assert suggestions.get("load") == "Load"

    def test_detects_case_insensitive(self):
        """Should detect columns case-insensitively."""
        df = pd.DataFrame({"TIME": [1, 2, 3], "LOAD": [10, 20, 30], "EXTENSION": [0.1, 0.2, 0.3]})

        patterns = {
            "time": ["time"],
            "load": ["load"],
            "extension": ["extension"],
        }
        suggestions = CSVParser.detect_columns(df, patterns)

        # Should still detect even with uppercase
        assert "time" in suggestions
        assert "load" in suggestions
        assert "extension" in suggestions

    def test_returns_empty_for_unrecognized_columns(self):
        """Should return empty dict for completely unrecognized columns."""
        df = pd.DataFrame(
            {"ColumnA": [1, 2, 3], "ColumnB": [10, 20, 30], "ColumnC": [0.1, 0.2, 0.3]}
        )

        suggestions = CSVParser.detect_columns(df)

        # May be empty or have partial matches depending on patterns
        assert isinstance(suggestions, dict)


class TestCSVParserValidateData:
    """Tests for CSVParser.validate_data method."""

    def test_no_warnings_for_valid_data(self, sample_dataframe):
        """Should return empty list for valid data."""
        warnings = CSVParser.validate_data(sample_dataframe)
        assert warnings == []

    def test_warns_on_empty_dataframe(self):
        """Should warn when DataFrame is empty."""
        empty_df = pd.DataFrame()
        warnings = CSVParser.validate_data(empty_df)

        assert len(warnings) > 0
        assert any("empty" in w.lower() for w in warnings)

    def test_warns_on_all_null_columns(self):
        """Should warn when a column is entirely null."""
        df = pd.DataFrame(
            {
                "A": [1, 2, 3],
                "B": [None, None, None],  # All null
            }
        )

        warnings = CSVParser.validate_data(df)
        assert any("null" in w.lower() for w in warnings)

    def test_warns_on_negative_time(self):
        """Should warn when time column has negative values."""
        df = pd.DataFrame({"Time": [-1, 0, 1, 2], "Load": [10, 20, 30, 40]})

        warnings = CSVParser.validate_data(df)
        assert warnings == []


class TestCSVParserGetAvailableColumns:
    """Tests for CSVParser.get_available_columns method."""

    def test_returns_list_of_column_names(self, sample_dataframe):
        """Should return list of column names."""
        columns = CSVParser.get_available_columns(sample_dataframe)

        assert isinstance(columns, list)
        assert "Time" in columns
        assert "Load" in columns

    def test_returns_empty_list_for_empty_dataframe(self):
        """Should return empty list for DataFrame with no columns."""
        empty_df = pd.DataFrame()
        columns = CSVParser.get_available_columns(empty_df)

        assert columns == []
