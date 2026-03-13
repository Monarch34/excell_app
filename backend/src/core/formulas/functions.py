"""
Safe functions for formula evaluation.

This module defines whitelisted mathematical functions that can be used
in user-defined formulas. All functions work on numpy arrays/pandas Series
for vectorized operations.
"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

_logger = logging.getLogger(__name__)


def _safe_sqrt(x: Any) -> Any:
    """Square root with domain-error warning for negative values."""
    result = np.sqrt(x)
    arr = np.asarray(result)
    if np.any(np.isnan(arr)) and not np.all(np.isnan(np.asarray(x, dtype=float))):
        _logger.warning("SQRT received negative value(s); returning NaN for those entries")
    return result


def _safe_log(x: Any) -> Any:
    """Natural log with domain-error warning for non-positive values."""
    result = np.log(x)
    arr = np.asarray(result)
    if np.any(np.isnan(arr) | np.isinf(arr)):
        x_arr = np.asarray(x, dtype=float)
        if np.any(x_arr <= 0):
            _logger.warning("LOG received non-positive value(s); returning NaN/inf for those entries")
    return result


def _safe_log10(x: Any) -> Any:
    """Base-10 log with domain-error warning for non-positive values."""
    result = np.log10(x)
    arr = np.asarray(result)
    if np.any(np.isnan(arr) | np.isinf(arr)):
        x_arr = np.asarray(x, dtype=float)
        if np.any(x_arr <= 0):
            _logger.warning("LOG10 received non-positive value(s); returning NaN/inf for those entries")
    return result


def _compliment_fn(x: Any) -> Any:
    """
    COMPLIMENT/COMPLEMENT function for formulas.

    Switches the sign of numeric values:
    - COMPLIMENT(10) -> -10
    - COMPLIMENT(-3) -> 3
    Works for both scalars and arrays.
    """
    return np.negative(x)


def _min_fn(*args: Any) -> Any:
    """
    MIN function for formulas.

    - MIN(x): scalar minimum over a vector/series
    - MIN(x, y, ...): element-wise minimum
    """
    if len(args) == 0:
        raise TypeError("MIN() requires at least 1 argument")
    if len(args) == 1:
        arr = np.asarray(args[0], dtype=float)
        if arr.size == 0 or np.all(np.isnan(arr)):
            return np.nan
        return float(np.nanmin(arr))
    result = args[0]
    for value in args[1:]:
        result = np.minimum(result, value)
    return result


def _max_fn(*args: Any) -> Any:
    """
    MAX function for formulas.

    - MAX(x): scalar maximum over a vector/series
    - MAX(x, y, ...): element-wise maximum
    """
    if len(args) == 0:
        raise TypeError("MAX() requires at least 1 argument")
    if len(args) == 1:
        arr = np.asarray(args[0], dtype=float)
        if arr.size == 0 or np.all(np.isnan(arr)):
            return np.nan
        return float(np.nanmax(arr))
    result = args[0]
    for value in args[1:]:
        result = np.maximum(result, value)
    return result


# Safe mathematical functions for formula evaluation
# These are the ONLY functions allowed in user formulas
SAFE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    # Basic math
    "ABS": np.abs,
    "SQRT": _safe_sqrt,
    # Logarithms and exponentials
    "LOG": _safe_log,  # Natural logarithm
    "LOG10": _safe_log10,  # Base-10 logarithm
    "EXP": np.exp,  # e^x
    # Rounding
    "ROUND": np.round,
    "FLOOR": np.floor,
    "CEIL": np.ceil,
    # Power
    "POW": np.power,
    # Min/max:
    # - 1 arg -> scalar aggregate
    # - 2+ args -> element-wise comparison
    "MIN": _min_fn,
    "MAX": _max_fn,
    # Aggregation (reduces vector to scalar)
    "SUM": np.nansum,
    "AVERAGE": np.nanmean,
    "MEAN": np.nanmean,
    "MEDIAN": np.nanmedian,
    "COUNT": lambda x: float(np.sum(~np.isnan(np.asarray(x, dtype=float)))),
    "STDEV": np.nanstd,
    "COMPLIMENT": _compliment_fn,
    "COMPLEMENT": _compliment_fn,
}


# Safe operators (simpleeval default + power)
SAFE_OPERATORS = {
    "+",
    "-",
    "*",
    "/",
    "**",
    "^",
    "(",
    ")",
}


def get_function_help() -> str:
    """Return help text describing available functions."""
    return """
Available Functions:
  ABS(x)       - Absolute value
  SQRT(x)      - Square root
  LOG(x)       - Natural logarithm (ln)
  LOG10(x)     - Base-10 logarithm
  EXP(x)       - Exponential (e^x)
  ROUND(x, n)  - Round to n decimal places
  FLOOR(x)     - Round down to integer
  CEIL(x)      - Round up to integer
  POW(x, y)    - Power (x^y)
  MIN(x)       - Minimum value of vector (scalar)
  MIN(x, y)    - Element-wise minimum
  MAX(x)       - Maximum value of vector (scalar)
  MAX(x, y)    - Element-wise maximum
  SUM(x)       - Sum of all values (reduces to scalar)
  AVERAGE(x)   - Mean of all values (reduces to scalar)
  MEAN(x)      - Alias for AVERAGE
  MEDIAN(x)    - Median value (reduces to scalar)
  COUNT(x)     - Number of values (reduces to scalar)
  STDEV(x)     - Standard deviation (reduces to scalar)
  COMPLIMENT(x)- Invert sign of value(s) (alias: COMPLEMENT)

Reference Functions:
  REF([Column]) - Value of column at reference row (scalar)

Operators:
  +, -, *, /   - Basic arithmetic
  ^, **        - Exponentiation
  ( )          - Parentheses for grouping

Column References:
  [Column Name] - Reference a column or parameter by its exact name

Examples:
  [A] + [B]                  - Add two columns
  [A] / [B] * 100            - Percentage calculation
  SQRT([A])                  - Square root of column
  SUM([A])                   - Total of column (scalar result)
  [A] - REF([A])             - Offset from reference row
  AVERAGE([A]) * [Param]     - Aggregation with parameter
"""
