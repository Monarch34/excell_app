"""
Unit tests for src/api/validators.py

Tests filename validation, numeric validation, and parameter validation.
"""

import pytest
from fastapi import HTTPException

from src.api.validators import validate_filename, validate_numeric, validate_parameters


class TestValidateFilename:
    def test_valid_csv_filename(self):
        assert validate_filename("data.csv") == "data.csv"

    def test_strips_whitespace(self):
        assert validate_filename("  data.csv  ") == "data.csv"

    def test_empty_string_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("")
        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail.lower()

    def test_none_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename(None)
        assert exc_info.value.status_code == 400

    def test_whitespace_only_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("   ")
        assert exc_info.value.status_code == 400

    def test_too_long_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("a" * 252 + ".csv")
        assert exc_info.value.status_code == 400
        assert "long" in exc_info.value.detail.lower()

    def test_exactly_255_chars_ok(self):
        name = "a" * 251 + ".csv"
        assert len(name) == 255
        assert validate_filename(name) == name

    def test_control_char_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("data\x00.csv")
        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    def test_tab_char_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("data\t.csv")
        assert exc_info.value.status_code == 400

    def test_path_separator_forward_slash_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("dir/data.csv")
        assert exc_info.value.status_code == 400
        assert "path" in exc_info.value.detail.lower()

    def test_path_separator_backslash_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("dir\\data.csv")
        assert exc_info.value.status_code == 400

    def test_path_traversal_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("../data.csv")
        assert exc_info.value.status_code == 400

    def test_disallowed_extension_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("data.xlsx")
        assert exc_info.value.status_code == 400
        assert ".csv" in exc_info.value.detail.lower()

    def test_no_extension_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_filename("data")
        assert exc_info.value.status_code == 400

    def test_special_chars_in_name_ok(self):
        assert validate_filename("my-data_v2 (final).csv") == "my-data_v2 (final).csv"


class TestValidateNumeric:
    def test_valid_number(self):
        validate_numeric(3.14, "width")

    def test_none_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_numeric(None, "width")
        assert exc_info.value.status_code == 400

    def test_nan_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_numeric(float("nan"), "width")
        assert exc_info.value.status_code == 400
        assert "finite" in exc_info.value.detail.lower()

    def test_inf_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_numeric(float("inf"), "width")
        assert exc_info.value.status_code == 400

    def test_negative_inf_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            validate_numeric(float("-inf"), "width")
        assert exc_info.value.status_code == 400

    def test_zero_is_valid(self):
        validate_numeric(0, "width")

    def test_negative_is_valid(self):
        validate_numeric(-5.0, "offset")


class TestValidateParameters:
    def test_empty_dict_is_noop(self):
        validate_parameters({})

    def test_none_values_skipped(self):
        validate_parameters({"width": None, "length": 10.0})

    def test_invalid_value_raises(self):
        with pytest.raises(HTTPException):
            validate_parameters({"width": float("nan")})

    def test_rule_max_exceeded(self):
        rules = {"width": {"max": 100}}
        with pytest.raises(HTTPException) as exc_info:
            validate_parameters({"width": 200}, rules=rules)
        assert exc_info.value.status_code == 400
        assert "large" in exc_info.value.detail.lower()

    def test_rule_max_not_exceeded(self):
        rules = {"width": {"max": 100}}
        validate_parameters({"width": 50}, rules=rules)

    def test_rule_key_case_insensitive(self):
        rules = {"width": {"max": 100}}
        with pytest.raises(HTTPException):
            validate_parameters({"Width": 200}, rules=rules)
