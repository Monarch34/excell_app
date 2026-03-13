"""
Unit tests for src/services/formula_context.py

Tests reference normalization, alias building, fuzzy matching,
formula rewriting, and apply_cut_point.
"""

import numpy as np
import pandas as pd
import pytest

from src.services.formula_context import (
    apply_cut_point,
    build_formula_alias_maps,
    normalize_ref_name,
    resolve_fuzzy_reference,
    rewrite_formula_references,
)
from src.core.formulas.engine import UserFormula


class TestNormalizeRefName:
    def test_strips_and_lowercases(self):
        assert normalize_ref_name("  Tensile Stress  ") == "tensile stress"

    def test_collapses_internal_whitespace(self):
        assert normalize_ref_name("Tensile   strain") == "tensile strain"

    def test_empty_string(self):
        assert normalize_ref_name("") == ""

    def test_whitespace_only(self):
        assert normalize_ref_name("   ") == ""

    def test_non_string_coerced(self):
        assert normalize_ref_name(42) == "42"


class TestBuildFormulaAliasMaps:
    def test_basic_columns(self):
        exact, normalized = build_formula_alias_maps(["Load", "Time"])
        assert normalized == {"load": "Load", "time": "Time"}
        assert exact == {}

    def test_empty_columns(self):
        exact, normalized = build_formula_alias_maps([])
        assert exact == {}
        assert normalized == {}

    def test_parameters_included(self):
        _, normalized = build_formula_alias_maps(
            ["Load"], available_parameters=["Length"]
        )
        assert "length" in normalized
        assert "load" in normalized

    def test_header_mapping_creates_exact_alias(self):
        exact, normalized = build_formula_alias_maps(
            ["col_internal"],
            header_mapping={"col_internal": "Display Label"},
        )
        assert exact["Display Label"] == "col_internal"
        assert normalized["display label"] == "col_internal"

    def test_skips_non_string_items(self):
        _, normalized = build_formula_alias_maps([None, 42, "Valid"])
        assert normalized == {"valid": "Valid"}

    def test_first_normalized_name_wins(self):
        _, normalized = build_formula_alias_maps(["Load", "load"])
        assert normalized["load"] == "Load"

    def test_header_mapping_with_empty_label_skipped(self):
        exact, _ = build_formula_alias_maps(
            ["col"], header_mapping={"col": "  "}
        )
        assert exact == {}


class TestResolveFuzzyReference:
    def test_returns_close_match(self):
        result = resolve_fuzzy_reference(
            "Tensile stress", ["Tensile stress (MPa)", "Time"]
        )
        assert result == "Tensile stress (MPa)"

    def test_returns_none_below_threshold(self):
        result = resolve_fuzzy_reference("ZZZZZ", ["Load", "Time"])
        assert result is None

    def test_returns_none_for_empty_candidates(self):
        assert resolve_fuzzy_reference("Load", []) is None

    def test_returns_none_for_empty_token(self):
        assert resolve_fuzzy_reference("", ["Load"]) is None

    def test_returns_none_when_two_scores_are_tied(self):
        result = resolve_fuzzy_reference("Stress", ["Stress A", "Stress B"])
        assert result is None

    def test_word_overlap_bonus(self):
        result = resolve_fuzzy_reference(
            "tensile extension",
            ["Tensile extension (mm)", "Extension sensor", "Tensile strain (mm/mm)"],
        )
        assert result == "Tensile extension (mm)"


class TestRewriteFormulaReferences:
    def test_empty_formula(self):
        assert rewrite_formula_references("", ["A"]) == ""

    def test_no_bracket_references(self):
        assert rewrite_formula_references("1 + 2", ["A"]) == "1 + 2"

    def test_exact_column_match(self):
        result = rewrite_formula_references("[Load] * 2", ["Load", "Time"])
        assert result == "[Load] * 2"

    def test_normalized_match(self):
        result = rewrite_formula_references("[LOAD] * 2", ["Load", "Time"])
        assert result == "[Load] * 2"

    def test_strict_preserves_unknown_refs(self):
        result = rewrite_formula_references(
            "[Unknown] * 2", ["Load"], strict=True
        )
        assert result == "[Unknown] * 2"

    def test_non_strict_uses_fuzzy(self):
        result = rewrite_formula_references(
            "[Tensile stress] * 2",
            ["Tensile stress (MPa)", "Time"],
            strict=False,
        )
        assert result == "[Tensile stress (MPa)] * 2"

    def test_header_mapping_exact_alias(self):
        result = rewrite_formula_references(
            "[Stress Label] / 100",
            ["stress_col"],
            header_mapping={"stress_col": "Stress Label"},
        )
        assert result == "[stress_col] / 100"


class TestApplyCutPoint:
    @pytest.fixture()
    def simple_df(self):
        return pd.DataFrame({"X": [1, 2, 3, 4, 5], "Y": [10, 20, 30, 40, 50]})

    @pytest.fixture()
    def add_formula(self):
        return [UserFormula(name="Z", formula="[Y] + 1")]

    def test_none_reference_applies_to_entire_df(self, simple_df, add_formula):
        result = apply_cut_point(simple_df, add_formula, {}, reference_index=None)
        assert "Z" in result.columns
        assert list(result["Z"]) == [11, 21, 31, 41, 51]

    def test_negative_reference_applies_to_entire_df(self, simple_df, add_formula):
        result = apply_cut_point(simple_df, add_formula, {}, reference_index=-1)
        assert list(result["Z"]) == [11, 21, 31, 41, 51]

    def test_reference_at_zero(self, simple_df, add_formula):
        result = apply_cut_point(simple_df, add_formula, {}, reference_index=0)
        assert "Z" in result.columns
        assert all(np.isfinite(result["Z"]))

    def test_reference_in_middle(self, simple_df, add_formula):
        result = apply_cut_point(simple_df, add_formula, {}, reference_index=2)
        assert np.isnan(result["Z"].iloc[0])
        assert np.isnan(result["Z"].iloc[1])
        assert np.isfinite(result["Z"].iloc[2])

    def test_reference_out_of_bounds(self, simple_df, add_formula):
        result = apply_cut_point(simple_df, add_formula, {}, reference_index=100)
        assert "Z" in result.columns
        assert all(np.isnan(result["Z"]))

    def test_empty_formulas(self, simple_df):
        result = apply_cut_point(simple_df, [], {}, reference_index=2)
        assert list(result.columns) == ["X", "Y"]
