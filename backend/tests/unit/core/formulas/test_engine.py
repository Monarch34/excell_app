"""
Tests for FormulaEngine.
"""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import pytest
from src.core.formulas import FormulaEngine, UserFormula


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "A": [1.0, 2.0, 3.0, 4.0, 5.0],
            "B": [10.0, 20.0, 30.0, 40.0, 50.0],
            "C": [100.0, 200.0, 300.0, 400.0, 500.0],
        }
    )


@pytest.fixture
def engine():
    """Create a FormulaEngine instance."""
    return FormulaEngine()


class TestFormulaEngineEvaluate:
    """Tests for evaluate method."""

    def test_simple_addition(self, engine, sample_df):
        result = engine.evaluate("[A] + [B]", sample_df)
        expected = pd.Series([11.0, 22.0, 33.0, 44.0, 55.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_simple_subtraction(self, engine, sample_df):
        result = engine.evaluate("[B] - [A]", sample_df)
        expected = pd.Series([9.0, 18.0, 27.0, 36.0, 45.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_multiplication(self, engine, sample_df):
        result = engine.evaluate("[A] * [B]", sample_df)
        expected = pd.Series([10.0, 40.0, 90.0, 160.0, 250.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_division(self, engine, sample_df):
        result = engine.evaluate("[B] / [A]", sample_df)
        expected = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_exponentiation_double_star(self, engine, sample_df):
        result = engine.evaluate("[A] ** 2", sample_df)
        expected = pd.Series([1.0, 4.0, 9.0, 16.0, 25.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_exponentiation_caret(self, engine, sample_df):
        result = engine.evaluate("[A] ^ 2", sample_df)
        expected = pd.Series([1.0, 4.0, 9.0, 16.0, 25.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_parentheses(self, engine, sample_df):
        result = engine.evaluate("([A] + [B]) * 2", sample_df)
        expected = pd.Series([22.0, 44.0, 66.0, 88.0, 110.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_constant_in_formula(self, engine, sample_df):
        result = engine.evaluate("[A] + 100", sample_df)
        expected = pd.Series([101.0, 102.0, 103.0, 104.0, 105.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_invalid_column_raises(self, engine, sample_df):
        with pytest.raises(ValueError) as exc_info:
            engine.evaluate("[Unknown]", sample_df)
        assert "Unknown" in str(exc_info.value)

    def test_evaluate_is_thread_safe_for_parallel_calls(self, sample_df):
        engine = FormulaEngine()
        expected = pd.Series([21.0, 42.0, 63.0, 84.0, 105.0])

        def evaluate_once(_: int) -> pd.Series:
            result = engine.evaluate("[A] + ([B] * 2)", sample_df)
            assert isinstance(result, pd.Series)
            return result

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(evaluate_once, range(24)))

        for result in results:
            pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_exponent_too_large_raises(self, engine, sample_df):
        """Exponent > 1000 should raise ValueError."""
        with pytest.raises(ValueError, match="Exponent too large"):
            engine.evaluate("[A] ** 1001", sample_df)

    def test_reasonable_exponent_works(self, engine, sample_df):
        """Exponent within limit should work fine."""
        result = engine.evaluate("[A] ** 3", sample_df)
        expected = pd.Series([1.0, 8.0, 27.0, 64.0, 125.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)


class TestFormulaEngineFunctions:
    """Tests for mathematical functions."""

    def test_abs_function(self, engine):
        df = pd.DataFrame({"A": [-1.0, -2.0, 3.0, -4.0, 5.0]})
        result = engine.evaluate("ABS([A])", df)
        expected = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_sqrt_function(self, engine):
        df = pd.DataFrame({"A": [1.0, 4.0, 9.0, 16.0, 25.0]})
        result = engine.evaluate("SQRT([A])", df)
        expected = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_log_function(self, engine):
        df = pd.DataFrame({"A": [1.0, np.e, np.e**2]})
        result = engine.evaluate("LOG([A])", df)
        expected = pd.Series([0.0, 1.0, 2.0])
        pd.testing.assert_series_equal(result, expected, check_names=False, atol=1e-10)

    def test_log10_function(self, engine):
        df = pd.DataFrame({"A": [1.0, 10.0, 100.0]})
        result = engine.evaluate("LOG10([A])", df)
        expected = pd.Series([0.0, 1.0, 2.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_exp_function(self, engine):
        df = pd.DataFrame({"A": [0.0, 1.0, 2.0]})
        result = engine.evaluate("EXP([A])", df)
        expected = pd.Series([1.0, np.e, np.e**2])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_round_function(self, engine):
        df = pd.DataFrame({"A": [1.234, 2.567, 3.891]})
        result = engine.evaluate("ROUND([A], 1)", df)
        expected = pd.Series([1.2, 2.6, 3.9])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_floor_function(self, engine):
        df = pd.DataFrame({"A": [1.9, 2.1, 3.5]})
        result = engine.evaluate("FLOOR([A])", df)
        expected = pd.Series([1.0, 2.0, 3.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_ceil_function(self, engine):
        df = pd.DataFrame({"A": [1.1, 2.9, 3.0]})
        result = engine.evaluate("CEIL([A])", df)
        expected = pd.Series([2.0, 3.0, 3.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_pow_function(self, engine):
        df = pd.DataFrame({"A": [2.0, 3.0, 4.0]})
        result = engine.evaluate("POW([A], 3)", df)
        expected = pd.Series([8.0, 27.0, 64.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_min_function(self, engine, sample_df):
        result = engine.evaluate("MIN([A], [B])", sample_df)
        expected = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_max_function(self, engine, sample_df):
        result = engine.evaluate("MAX([A], [B])", sample_df)
        expected = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_max_single_argument_aggregation(self, engine, sample_df):
        result = engine.evaluate("MAX([B])", sample_df)
        assert result == pytest.approx(50.0)

    def test_min_single_argument_aggregation(self, engine, sample_df):
        result = engine.evaluate("MIN([B])", sample_df)
        assert result == pytest.approx(10.0)

    def test_sum_aggregation_ignores_nan(self, engine):
        df = pd.DataFrame({"A": [1.0, np.nan, 3.0]})
        result = engine.evaluate("SUM([A])", df)
        assert result == pytest.approx(4.0)

    def test_average_aggregation_ignores_nan(self, engine):
        df = pd.DataFrame({"A": [2.0, np.nan, 4.0]})
        result = engine.evaluate("AVERAGE([A])", df)
        assert result == pytest.approx(3.0)

    def test_median_aggregation_ignores_nan(self, engine):
        df = pd.DataFrame({"A": [1.0, np.nan, 3.0, 9.0]})
        result = engine.evaluate("MEDIAN([A])", df)
        assert result == pytest.approx(3.0)

    def test_count_aggregation_counts_non_nan_values(self, engine):
        df = pd.DataFrame({"A": [1.0, np.nan, 3.0, np.nan]})
        result = engine.evaluate("COUNT([A])", df)
        assert result == pytest.approx(2.0)

    def test_compliment_function_switches_sign(self, engine):
        df = pd.DataFrame({"A": [1.0, -2.0, 0.0]})
        result = engine.evaluate("COMPLIMENT([A])", df)
        expected = pd.Series([-1.0, 2.0, -0.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_complement_alias_switches_sign(self, engine):
        df = pd.DataFrame({"A": [1.0, -2.0, 0.0]})
        result = engine.evaluate("COMPLEMENT([A])", df)
        expected = pd.Series([-1.0, 2.0, -0.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)


class TestFormulaEngineApplyFormulas:
    """Tests for apply_formulas method."""

    def test_apply_single_formula(self, engine, sample_df):
        formula = UserFormula(name="Sum", formula="[A] + [B]")
        result = engine.apply_formulas(sample_df, [formula])

        assert "Sum" in result.columns
        expected = pd.Series([11.0, 22.0, 33.0, 44.0, 55.0], name="Sum")
        pd.testing.assert_series_equal(result["Sum"], expected)

    def test_apply_multiple_formulas(self, engine, sample_df):
        formulas = [
            UserFormula(name="Sum", formula="[A] + [B]"),
            UserFormula(name="Product", formula="[A] * [B]"),
        ]
        result = engine.apply_formulas(sample_df, [formulas[0]])
        result = engine.apply_formulas(result, [formulas[1]])

        assert "Sum" in result.columns
        assert "Product" in result.columns

    def test_formula_can_reference_previous_formula_column(self, engine, sample_df):
        formulas = [
            UserFormula(name="Sum", formula="[A] + [B]"),
        ]
        result = engine.apply_formulas(sample_df, formulas)

        # Now create a formula that references Sum
        formula2 = UserFormula(name="DoubleSum", formula="[Sum] * 2")
        result = engine.apply_formulas(result, [formula2])

        assert "DoubleSum" in result.columns
        expected = pd.Series([22.0, 44.0, 66.0, 88.0, 110.0], name="DoubleSum")
        pd.testing.assert_series_equal(result["DoubleSum"], expected)

    def test_original_df_not_modified(self, engine, sample_df):
        original_columns = sample_df.columns.tolist()
        formula = UserFormula(name="Sum", formula="[A] + [B]")

        engine.apply_formulas(sample_df, [formula])

        assert sample_df.columns.tolist() == original_columns

    def test_empty_formula_list(self, engine, sample_df):
        result = engine.apply_formulas(sample_df, [])
        pd.testing.assert_frame_equal(result, sample_df)

    def test_max_formulas_limit(self, engine, sample_df):
        formulas = [
            UserFormula(name=f"Col{i}", formula="[A] + [B]") for i in range(engine.MAX_FORMULAS + 1)
        ]

        with pytest.raises(ValueError) as exc_info:
            engine.apply_formulas(sample_df, formulas)
        assert "Too many formulas" in str(exc_info.value)


class TestFormulaEngineGetReferencedColumns:
    """Tests for get_referenced_columns method."""

    def test_get_referenced_columns(self, engine):
        result = engine.get_referenced_columns("[A] + [B] * [C]")
        assert set(result) == {"A", "B", "C"}
