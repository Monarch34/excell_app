"""
Tests for REF() function in FormulaEngine.
"""

import pandas as pd
import pytest
from src.core.formulas import FormulaEngine, UserFormula


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Load": [5.0, 10.0, 15.0, 20.0, 25.0],
            "Extension": [0.0, 0.5, 1.0, 1.5, 2.0],
            "Time": [0.0, 1.0, 2.0, 3.0, 4.0],
        }
    )


@pytest.fixture
def engine():
    """Create a FormulaEngine instance."""
    return FormulaEngine()


class TestREFFunction:
    """Tests for REF() function."""

    def test_ref_returns_value_at_reference_index(self, engine, sample_df):
        """REF([Load]) should return a scalar value at reference row."""
        result = engine.evaluate("REF([Load])", sample_df, reference_index=2)
        # Reference index 2 has Load=15.0, result is scalar
        assert isinstance(result, float)
        assert result == 15.0

    def test_ref_subtraction_formula(self, engine, sample_df):
        """[Load] - REF([Load]) should compute offset from reference."""
        result = engine.evaluate("[Load] - REF([Load])", sample_df, reference_index=2)
        # Load values are [5, 10, 15, 20, 25], ref is 15
        # Expected: [5-15, 10-15, 15-15, 20-15, 25-15] = [-10, -5, 0, 5, 10]
        expected = pd.Series([-10.0, -5.0, 0.0, 5.0, 10.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_ref_with_no_reference_index_raises_error(self, engine, sample_df):
        """REF without reference_index should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            engine.evaluate("REF([Load])", sample_df, reference_index=None)
        assert "requires a reference row" in str(exc_info.value)

    def test_ref_with_out_of_bounds_index_raises_error(self, engine, sample_df):
        """REF with invalid index should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            engine.evaluate("REF([Load])", sample_df, reference_index=100)
        assert "out of bounds" in str(exc_info.value)

    def test_ref_with_negative_index_raises_error(self, engine, sample_df):
        """REF with negative index should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            engine.evaluate("REF([Load])", sample_df, reference_index=-1)
        assert "out of bounds" in str(exc_info.value)

    def test_ref_first_row_reference(self, engine, sample_df):
        """REF with reference_index=0 should use first row."""
        result = engine.evaluate("[Load] - REF([Load])", sample_df, reference_index=0)
        # Load values are [5, 10, 15, 20, 25], ref is 5
        expected = pd.Series([0.0, 5.0, 10.0, 15.0, 20.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_ref_last_row_reference(self, engine, sample_df):
        """REF with reference_index=last should use last row."""
        result = engine.evaluate("[Load] - REF([Load])", sample_df, reference_index=4)
        # Load values are [5, 10, 15, 20, 25], ref is 25
        expected = pd.Series([-20.0, -15.0, -10.0, -5.0, 0.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_multiple_ref_in_formula(self, engine, sample_df):
        """Formula can use multiple REF functions."""
        result = engine.evaluate(
            "[Load] - REF([Load]) + [Extension] - REF([Extension])", sample_df, reference_index=2
        )
        # Load: [5,10,15,20,25] - 15 = [-10,-5,0,5,10]
        # Extension: [0,0.5,1.0,1.5,2.0] - 1.0 = [-1,-0.5,0,0.5,1.0]
        # Sum: [-11, -5.5, 0, 5.5, 11]
        expected = pd.Series([-11.0, -5.5, 0.0, 5.5, 11.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)

    def test_ref_with_parameters(self, engine, sample_df):
        """REF should work alongside parameters."""
        result = engine.evaluate(
            "([Load] - REF([Load])) / [area]",
            sample_df,
            parameters={"area": 10.0},
            reference_index=2,
        )
        # (Load - 15) / 10 = [-1.0, -0.5, 0, 0.5, 1.0]
        expected = pd.Series([-1.0, -0.5, 0.0, 0.5, 1.0])
        pd.testing.assert_series_equal(result, expected, check_names=False)


class TestApplyFormulasWithREF:
    """Tests for apply_formulas with REF() function."""

    def test_apply_formulas_with_ref(self, engine, sample_df):
        """apply_formulas should pass reference_index correctly."""
        formulas = [
            UserFormula(name="new_load", formula="[Load] - REF([Load])"),
            UserFormula(name="new_ext", formula="[Extension] - REF([Extension])"),
        ]
        result = engine.apply_formulas(sample_df, formulas, reference_index=2)

        assert "new_load" in result.columns
        assert "new_ext" in result.columns

        # new_load at reference (row 2) should be 0
        assert result["new_load"].iloc[2] == 0.0
        assert result["new_ext"].iloc[2] == 0.0

    def test_apply_chained_formulas_with_ref(self, engine, sample_df):
        """Chained formulas can reference columns created with REF."""
        formulas = [
            UserFormula(name="new_load", formula="[Load] - REF([Load])"),
        ]
        result = engine.apply_formulas(sample_df, formulas, reference_index=2)

        # Now create a formula referencing new_load
        formula2 = [
            UserFormula(name="stress", formula="[new_load] / 10"),
        ]
        result = engine.apply_formulas(result, formula2, reference_index=2)

        assert "stress" in result.columns
        expected_stress = pd.Series([-1.0, -0.5, 0.0, 0.5, 1.0], name="stress")
        pd.testing.assert_series_equal(result["stress"], expected_stress)
