"""
Formula Engine module for user-defined calculations.

This module provides a safe way for users to define custom calculated
columns using a simple formula syntax with mathematical functions.

Example:
    >>> from src.core.formulas import FormulaEngine, UserFormula
    >>> engine = FormulaEngine()
    >>> formula = UserFormula(
    ...     name="Ratio",
    ...     formula="[A] / [B]"
    ... )
    >>> result_df = engine.apply_formulas(df, [formula])
"""

from .engine import FormulaEngine, UserFormula
from .functions import SAFE_FUNCTIONS, get_function_help
from .validator import FormulaValidator

__all__ = [
    "FormulaEngine",
    "UserFormula",
    "SAFE_FUNCTIONS",
    "FormulaValidator",
    "get_function_help",
]
