"""
Formula Engine for evaluating user-defined calculations.

This module provides a safe way to evaluate mathematical formulas
on DataFrame columns using the simpleeval library.
"""

import ast
import logging
import operator
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import simpleeval

from .functions import SAFE_FUNCTIONS
from .validator import FormulaValidator

logger = logging.getLogger(__name__)


def _safe_power(base, exp):
    """Exponentiation with a cap to prevent resource exhaustion."""
    if isinstance(exp, np.ndarray):
        if np.any(np.abs(exp) > 1000):
            raise ValueError("Exponent too large (absolute value must be <= 1000)")
    elif isinstance(exp, int | float) and abs(exp) > 1000:
        raise ValueError("Exponent too large (absolute value must be <= 1000)")
    return operator.pow(base, exp)


@dataclass
class UserFormula:
    """
    Represents a user-defined formula for creating a new column.

    Attributes:
        name: Name for the new column (must be unique)
        formula: Formula string using [Column Name] syntax
        unit: Optional unit string for the column (e.g., "(MPa)")
        description: Optional description of what the formula calculates

    Example:
        >>> formula = UserFormula(
        ...     name="Ratio",
        ...     formula="[A] / [B]",
        ...     unit="",
        ...     description="Ratio of two columns"
        ... )
    """

    name: str
    formula: str
    unit: str = ""
    description: str = ""


class FormulaEngine:
    """
    Engine for evaluating user-defined formulas safely.

    Uses simpleeval library with whitelisted functions for secure evaluation.
    Formulas reference DataFrame columns using [Column Name] syntax.

    Attributes:
        MAX_FORMULAS: Maximum number of formulas allowed (default 5)

    Example:
        >>> engine = FormulaEngine()
        >>> formula = UserFormula(name="Sum", formula="[A] + [B]")
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        >>> result_df = engine.apply_formulas(df, [formula])
        >>> list(result_df['Sum'])
        [5, 7, 9]
    """

    MAX_FORMULAS = 20
    MAX_FORMULA_LENGTH = 1000

    # Pattern to match column references: [Column Name]
    COLUMN_REF_PATTERN = re.compile(r"\[([^\]]+)\]")

    # Pattern to match REF function: REF([Column Name])
    REF_PATTERN = re.compile(r"REF\(\[([^\]]+)\]\)")

    def __init__(self):
        """Initialize the formula engine."""
        self._validator = FormulaValidator()
        simpleeval.MAX_STRING_LENGTH = 10_000
        simpleeval.MAX_COMPREHENSION_LENGTH = 1_000

        # Define numpy-compatible operators
        # simpleeval's default operators have safety checks that don't work with arrays
        self._numpy_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Pow: _safe_power,
            ast.Mod: operator.mod,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        logger.debug("FormulaEngine initialized with safe functions/operators")

    def validate(self, formula: str, available_columns: list[str]) -> list[str]:
        """
        Validate a formula string.

        Args:
            formula: The formula string to validate
            available_columns: List of available column names

        Returns:
            List of error messages. Empty list means valid.
        """
        return self._validator.validate(formula, available_columns)

    def _prepare_formula(
        self,
        formula: str,
        df: pd.DataFrame,
        parameters: dict[str, float] | None = None,
        reference_index: int | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Prepare formula for evaluation.

        Replaces [Column Name] references with safe variable names
        and creates a names dict mapping those variables to column data.
        Also handles REF([Column]) syntax to get value at reference row.

        Args:
            formula: Original formula string
            df: DataFrame containing the data
            parameters: Optional dict of parameter values
            reference_index: Optional index of reference row for REF() function

        Returns:
            Tuple of (prepared_formula, names_dict)
        """
        prepared_formula = formula
        names: dict[str, Any] = {}
        var_counter = 0

        # First, handle REF([Column]) patterns - must be done before regular column refs
        ref_matches = self.REF_PATTERN.findall(formula)
        for col_name in ref_matches:
            if col_name in df.columns:
                if reference_index is None:
                    raise ValueError(f"REF([{col_name}]) requires a reference row to be selected")
                if reference_index < 0 or reference_index >= len(df):
                    raise ValueError(f"Reference index {reference_index} is out of bounds")

                # Get the scalar value at reference index
                ref_value = df[col_name].iloc[reference_index]

                # Create safe variable name
                safe_name = f"ref_{var_counter}"
                var_counter += 1

                # Replace REF([Column]) with safe_name
                pattern = r"REF\(\[" + re.escape(col_name) + r"\]\)"
                prepared_formula = re.sub(pattern, safe_name, prepared_formula)

                # Broadcast scalar to array matching DataFrame length
                names[safe_name] = float(ref_value)

        # Find remaining column references (not inside REF())
        columns = self.COLUMN_REF_PATTERN.findall(prepared_formula)

        for col_name in columns:
            # Only process if it's a DataFrame column
            if col_name not in df.columns:
                continue

            # Create safe variable name
            safe_name = f"col_{var_counter}"
            var_counter += 1

            # Replace [Column Name] with safe_name
            pattern = r"\[" + re.escape(col_name) + r"\]"
            prepared_formula = re.sub(pattern, safe_name, prepared_formula)

            # Map safe_name to column data as numpy array
            names[safe_name] = df[col_name].to_numpy()

        # Inject parameters as constant arrays
        if parameters:
            for param_name, param_value in parameters.items():
                pattern = r"\[" + re.escape(param_name) + r"\]"
                if re.search(pattern, prepared_formula):
                    safe_name = f"param_{var_counter}"
                    var_counter += 1
                    prepared_formula = re.sub(pattern, safe_name, prepared_formula)
                    # Broadcast parameter to array matching DataFrame length
                    names[safe_name] = param_value

        # Replace ^ with ** for exponentiation
        prepared_formula = prepared_formula.replace("^", "**")

        return prepared_formula, names

    def evaluate(
        self,
        formula: str,
        df: pd.DataFrame,
        parameters: dict[str, float] | None = None,
        reference_index: int | None = None,
    ) -> "pd.Series | float":
        """
        Evaluate a formula against a DataFrame.

        Args:
            formula: Formula string using [Column Name] syntax
            df: DataFrame containing the referenced columns
            parameters: Optional dict of parameter name -> value for injection
            reference_index: Optional index of reference row for REF() function

        Returns:
            pd.Series for vector results, float for scalar results

        Raises:
            ValueError: If formula is invalid or evaluation fails
        """
        if len(formula) > self.MAX_FORMULA_LENGTH:
            raise ValueError(
                f"Formula exceeds maximum length of {self.MAX_FORMULA_LENGTH} characters"
            )

        if len(df) > 100_000:
            raise ValueError(
                f"DataFrame too large for formula evaluation ({len(df)} rows). "
                f"Maximum is 100,000 rows."
            )

        # Validate first -- include parameter names as available columns
        available_columns = df.columns.tolist()
        if parameters:
            available_columns.extend(parameters.keys())
        errors = self.validate(formula, available_columns)
        if errors:
            raise ValueError(f"Invalid formula: {'; '.join(errors)}")

        try:
            # Prepare formula and names
            prepared_formula, names = self._prepare_formula(
                formula, df, parameters, reference_index
            )

            # Build evaluator per call to avoid shared mutable state across requests.
            evaluator = simpleeval.SimpleEval(
                functions=SAFE_FUNCTIONS,
                names=names,
                operators=self._numpy_operators,
            )

            # Evaluate
            result = evaluator.eval(prepared_formula)

            # Return based on result type — let math determine scalar vs vector
            if isinstance(result, np.ndarray):
                if np.any(np.isinf(result)):
                    logger.warning(
                        f"Formula produced infinite values, replacing with NaN: {formula}"
                    )
                    result = np.where(np.isinf(result), np.nan, result)
                return pd.Series(result, index=df.index)
            elif isinstance(result, int | float | np.floating | np.integer):
                return float(result)
            else:
                return pd.Series(result, index=df.index)

        except ZeroDivisionError as e:
            raise ValueError("Division by zero: the formula divides by a value that is zero") from e
        except simpleeval.InvalidExpression as e:
            raise ValueError(f"Invalid expression: {e}") from e
        except simpleeval.FunctionNotDefined as e:
            raise ValueError(f"Unknown function: {e}") from e
        except simpleeval.NameNotDefined as e:
            raise ValueError(f"Unknown variable: {e}") from e
        except Exception as e:
            logger.exception(f"Formula evaluation failed: {formula}")
            raise ValueError(f"Evaluation error: {e}") from e

    def apply_formulas(
        self,
        df: pd.DataFrame,
        formulas: list[UserFormula],
        parameters: dict[str, float] | None = None,
        reference_index: int | None = None,
    ) -> pd.DataFrame:
        """
        Apply multiple formulas to a DataFrame.

        Each formula creates a new column in the DataFrame.
        Formulas are applied in order, so later formulas can
        reference columns created by earlier formulas.

        Args:
            df: Input DataFrame
            formulas: List of UserFormula objects to apply
            parameters: Optional dict of parameter name -> value for injection
            reference_index: Optional index of reference row for REF() function

        Returns:
            New DataFrame with formula columns added

        Raises:
            ValueError: If too many formulas or any formula fails
        """
        if len(formulas) > self.MAX_FORMULAS:
            raise ValueError(f"Too many formulas: {len(formulas)}. Maximum is {self.MAX_FORMULAS}")

        # Work on a copy
        result_df = df.copy()

        for formula_obj in formulas:
            logger.info(f"Applying formula: {formula_obj.name} = {formula_obj.formula}")

            try:
                # Evaluate formula with parameters and reference index
                series = self.evaluate(
                    formula_obj.formula,
                    result_df,
                    parameters=parameters,
                    reference_index=reference_index,
                )

                # Add as new column
                result_df[formula_obj.name] = series

                logger.debug(f"Formula '{formula_obj.name}' applied successfully")

            except ValueError as e:
                logger.error(f"Formula '{formula_obj.name}' failed: {e}")
                raise ValueError(f"Formula '{formula_obj.name}' failed: {e}") from e

        return result_df

    def get_referenced_columns(self, formula: str) -> list[str]:
        """
        Get list of columns referenced in a formula.

        Args:
            formula: Formula string

        Returns:
            List of column names referenced in the formula
        """
        return self._validator.get_referenced_columns(formula)
