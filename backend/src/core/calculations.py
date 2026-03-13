"""
Area calculation utilities using trapezoidal integration.

Mirrors the frontend implementation in areaCalculation.ts to ensure
consistent results between frontend and backend.
"""

from typing import Literal

import numpy as np

AreaMode = Literal["total", "positive", "negative"]


def trapezoidal_integral(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the trapezoidal integral of y with respect to x.
    Equivalent to numpy.trapezoid(y, x).

    Args:
        x: Array of x values
        y: Array of y values

    Returns:
        Integrated area under the curve
    """
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return 0.0

    # Use numpy's built-in trapezoid function for accuracy
    return float(np.trapezoid(y, x))


def filter_nan(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Filter out pairs where either x[i] or y[i] is NaN.

    Args:
        x: Array of x values
        y: Array of y values

    Returns:
        Tuple of (x_clean, y_clean) with NaN pairs removed
    """
    # Keep only finite pairs (filters NaN and +/-Inf)
    valid_mask = np.isfinite(x) & np.isfinite(y)
    return x[valid_mask], y[valid_mask]


def calculate_total_area(x: np.ndarray, y: np.ndarray, baseline: float = 0.0) -> float:
    """
    Calculate total signed area under the curve (baseline y=baseline).

    Args:
        x: Array of x values
        y: Array of y values
        baseline: Baseline y value (default: 0)

    Returns:
        Total signed area
    """
    x_clean, y_clean = filter_nan(x, y)
    if len(x_clean) < 2:
        return 0.0

    y_adj = y_clean - baseline
    return trapezoidal_integral(x_clean, y_adj)


def calculate_positive_area(x: np.ndarray, y: np.ndarray, baseline: float = 0.0) -> float:
    """
    Calculate area where y > baseline only (clips negative to 0).

    Args:
        x: Array of x values
        y: Array of y values
        baseline: Baseline y value (default: 0)

    Returns:
        Positive area only
    """
    x_clean, y_clean = filter_nan(x, y)
    if len(x_clean) < 2:
        return 0.0

    y_pos = np.maximum(y_clean - baseline, 0)
    if np.all(y_pos == 0):
        return 0.0

    return trapezoidal_integral(x_clean, y_pos)


def calculate_negative_area(x: np.ndarray, y: np.ndarray, baseline: float = 0.0) -> float:
    """
    Calculate area where y < baseline only (clips positive to 0, returns absolute value).

    Args:
        x: Array of x values
        y: Array of y values
        baseline: Baseline y value (default: 0)

    Returns:
        Absolute value of negative area
    """
    x_clean, y_clean = filter_nan(x, y)
    if len(x_clean) < 2:
        return 0.0

    y_neg = np.minimum(y_clean - baseline, 0)
    if np.all(y_neg == 0):
        return 0.0

    return abs(trapezoidal_integral(x_clean, y_neg))


def calculate_area(x: np.ndarray, y: np.ndarray, mode: AreaMode, baseline: float = 0.0) -> float:
    """
    Calculate area based on mode selection.

    Args:
        x: Array of x values
        y: Array of y values
        mode: Area calculation mode ('total', 'positive', 'negative')
        baseline: Baseline y value (default: 0)

    Returns:
        Calculated area based on mode
    """
    if mode == "total":
        return calculate_total_area(x, y, baseline)
    elif mode == "positive":
        return calculate_positive_area(x, y, baseline)
    elif mode == "negative":
        return calculate_negative_area(x, y, baseline)
    else:
        return 0.0


def calculate_region_area(
    x: np.ndarray, y: np.ndarray, x_baseline: float, y_baseline: float, region: str
) -> float:
    """
    Calculate area within a specific quadrant region.

    Args:
        x: Array of x values
        y: Array of y values
        x_baseline: X baseline value
        y_baseline: Y baseline value
        region: Region name ('top-left', 'top-right', 'bottom-left', 'bottom-right')

    Returns:
        Area within the specified region
    """
    x_clean, y_clean = filter_nan(x, y)
    if len(x_clean) < 2:
        return 0.0

    # Filter data to region bounds
    if region == "top-right":
        mask = (x_clean >= x_baseline) & (y_clean >= y_baseline)
    elif region == "top-left":
        mask = (x_clean <= x_baseline) & (y_clean >= y_baseline)
    elif region == "bottom-right":
        mask = (x_clean >= x_baseline) & (y_clean <= y_baseline)
    elif region == "bottom-left":
        mask = (x_clean <= x_baseline) & (y_clean <= y_baseline)
    else:
        return 0.0

    if not np.any(mask):
        return 0.0

    x_region = x_clean[mask]
    y_region = y_clean[mask]

    if len(x_region) < 2:
        return 0.0

    # Calculate area relative to baseline
    y_adj = y_region - y_baseline
    return trapezoidal_integral(x_region, y_adj)
