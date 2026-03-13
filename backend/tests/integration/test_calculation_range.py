"""
Tests for calculation range behavior - formulas only compute from reference row onwards.
"""

import pandas as pd
import pytest
from src.core.formulas.engine import FormulaEngine, UserFormula
from src.services.processing_service import ProcessingService


@pytest.fixture
def processing_service():
    """Create a ProcessingService instance."""
    return ProcessingService()


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Time": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
            "Load": [0.0, 5.0, 10.0, 15.0, 20.0, 25.0],
            "Extension": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
        }
    )


class TestCalculationRange:
    """Tests for calculation range filtering."""

    def test_no_reference_row_computes_all_rows(self, processing_service, sample_df):
        """Without reference row, all rows should have computed values."""
        formulas = [UserFormula(name="double_load", formula="[Load] * 2")]

        result_df, _ = processing_service.process(
            sample_df,
            operations=[],
            formulas=formulas,
            parameters={},
            initial_results={},  # No reference index
        )

        assert "double_load" in result_df.columns
        assert not result_df["double_load"].isna().any()

    def test_reference_row_limits_calculations(self, processing_service, sample_df):
        """With reference row, pre-reference rows should have NaN."""
        formulas = [UserFormula(name="double_load", formula="[Load] * 2")]

        result_df, _ = processing_service.process(
            sample_df,
            operations=[],
            formulas=formulas,
            parameters={},
            initial_results={"manual_reference_index": 3},  # Reference at row 3
        )

        assert "double_load" in result_df.columns

        # Rows 0, 1, 2 should be NaN
        assert result_df["double_load"].iloc[0] != result_df["double_load"].iloc[0]  # NaN check
        assert result_df["double_load"].iloc[1] != result_df["double_load"].iloc[1]
        assert result_df["double_load"].iloc[2] != result_df["double_load"].iloc[2]

        # Rows 3, 4, 5 should have computed values
        assert result_df["double_load"].iloc[3] == 30.0  # 15 * 2
        assert result_df["double_load"].iloc[4] == 40.0  # 20 * 2
        assert result_df["double_load"].iloc[5] == 50.0  # 25 * 2

    def test_reference_row_at_zero_computes_all(self, processing_service, sample_df):
        """Reference row at index 0 should compute all rows."""
        formulas = [UserFormula(name="double_load", formula="[Load] * 2")]

        result_df, _ = processing_service.process(
            sample_df,
            operations=[],
            formulas=formulas,
            parameters={},
            initial_results={"manual_reference_index": 0},
        )

        assert "double_load" in result_df.columns
        assert not result_df["double_load"].isna().any()

    def test_ref_function_with_calculation_range(self, processing_service, sample_df):
        """REF() function should work correctly with calculation range."""
        formulas = [UserFormula(name="load_offset", formula="[Load] - REF([Load])")]

        result_df, _ = processing_service.process(
            sample_df,
            operations=[],
            formulas=formulas,
            parameters={},
            initial_results={"manual_reference_index": 2},  # Reference at row 2 (Load=10)
        )

        assert "load_offset" in result_df.columns

        # Pre-reference rows should be NaN
        assert pd.isna(result_df["load_offset"].iloc[0])
        assert pd.isna(result_df["load_offset"].iloc[1])

        # From reference onwards: Load - REF(Load) where REF = 10
        assert result_df["load_offset"].iloc[2] == 0.0  # 10 - 10
        assert result_df["load_offset"].iloc[3] == 5.0  # 15 - 10
        assert result_df["load_offset"].iloc[4] == 10.0  # 20 - 10
        assert result_df["load_offset"].iloc[5] == 15.0  # 25 - 10

    def test_all_original_rows_preserved(self, processing_service, sample_df):
        """All original rows should be preserved for export."""
        original_len = len(sample_df)
        formulas = [UserFormula(name="double_load", formula="[Load] * 2")]

        result_df, _ = processing_service.process(
            sample_df,
            operations=[],
            formulas=formulas,
            parameters={},
            initial_results={"manual_reference_index": 3},
        )

        # Same number of rows as input
        assert len(result_df) == original_len

        # Original columns unchanged
        assert list(result_df["Time"]) == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        assert list(result_df["Load"]) == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]

    def test_too_many_derived_items_raises(self, processing_service, sample_df):
        formulas = [
            UserFormula(name=f"derived_{i}", formula="[Load] + 1")
            for i in range(FormulaEngine.MAX_FORMULAS + 1)
        ]

        with pytest.raises(ValueError, match="Too many derived items"):
            processing_service.process(
                sample_df,
                operations=[],
                formulas=formulas,
                parameters={},
                initial_results={},
            )

    def test_does_not_mutate_input_derived_parameter_formulas(self, processing_service, sample_df):
        derived_parameters = [{"name": "A0", "formula": "REF([Load])"}]
        original_formula = derived_parameters[0]["formula"]

        processing_service.process(
            sample_df,
            operations=[],
            formulas=[],
            parameters={},
            derived_parameters=derived_parameters,
            initial_results={"manual_reference_index": 0},
        )

        assert derived_parameters[0]["formula"] == original_formula
