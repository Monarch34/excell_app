from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


def normalize_regions(regions: list[str] | None) -> list[str]:
    return [region for region in (regions or []) if region != "all"]


def _build_region_mask(
    x_series: pd.Series,
    y_series: pd.Series,
    *,
    regions: list[str],
    x_baseline: float,
    y_baseline: float,
) -> pd.Series:
    mask = pd.Series(False, index=x_series.index)
    for region in regions:
        if region == "top-right":
            mask = mask | ((x_series >= x_baseline) & (y_series >= y_baseline))
        elif region == "top-left":
            mask = mask | ((x_series <= x_baseline) & (y_series >= y_baseline))
        elif region == "bottom-right":
            mask = mask | ((x_series >= x_baseline) & (y_series <= y_baseline))
        elif region == "bottom-left":
            mask = mask | ((x_series <= x_baseline) & (y_series <= y_baseline))
    return mask


def apply_scope_filters(
    df: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    scope: Any | None,
) -> pd.DataFrame:
    """Apply x and y scope filtering for a single y-series."""
    filtered = df
    if scope and getattr(scope, "mode", None) == "range":
        x_min = getattr(scope, "x_min", None)
        x_max = getattr(scope, "x_max", None)
        y_min = getattr(scope, "y_min", None)
        y_max = getattr(scope, "y_max", None)
        if x_min is not None:
            filtered = filtered[filtered[x_column] >= x_min]
        if x_max is not None:
            filtered = filtered[filtered[x_column] <= x_max]
        if y_min is not None:
            filtered = filtered[filtered[y_column] >= y_min]
        if y_max is not None:
            filtered = filtered[filtered[y_column] <= y_max]
    return filtered


def apply_baseline_region_filter_df(
    df: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    regions: list[str],
    x_baseline: float,
    y_baseline: float,
) -> pd.DataFrame:
    """Filter dataframe rows to selected baseline regions."""
    if not regions:
        return df

    x_series = pd.to_numeric(df[x_column], errors="coerce")
    y_series = pd.to_numeric(df[y_column], errors="coerce")
    region_mask = _build_region_mask(
        x_series,
        y_series,
        regions=regions,
        x_baseline=x_baseline,
        y_baseline=y_baseline,
    )

    return df[region_mask]


def filter_series_by_regions(
    x: pd.Series,
    y: pd.Series,
    *,
    regions: list[str],
    x_baseline: float,
    y_baseline: float,
) -> tuple[pd.Series, pd.Series]:
    if not regions:
        return x, y

    region_mask = _build_region_mask(
        x,
        y,
        regions=regions,
        x_baseline=x_baseline,
        y_baseline=y_baseline,
    )
    return x[region_mask], y[region_mask]


def filter_series_by_area_mode(
    x: pd.Series,
    y: pd.Series,
    *,
    chart_type: str,
    area_spec: dict[str, Any] | None,
    has_region_filter: bool,
) -> tuple[pd.Series, pd.Series]:
    """Apply area-mode filtering only when chart is area and no region filter is selected."""
    if chart_type != "area" or not area_spec or has_region_filter:
        return x, y

    mode = area_spec.get("mode")
    if mode not in ("positive", "negative"):
        return x, y

    baseline = float(area_spec.get("baseline") or 0.0)
    axis = area_spec.get("baseline_axis") or "y"
    if axis == "x":
        mask = x >= baseline if mode == "positive" else x <= baseline
    else:
        mask = y >= baseline if mode == "positive" else y <= baseline
    return x[mask], y[mask]


@dataclass
class AxisClamp:
    x_range: tuple[float, float] | None = None
    y_range: tuple[float, float] | None = None


def compute_region_axis_clamp(
    *,
    regions: list[str],
    x_baseline: float,
    y_baseline: float,
    min_x: float | None,
    max_x: float | None,
    min_y: float | None,
    max_y: float | None,
) -> AxisClamp:
    if not regions:
        return AxisClamp()

    has_left = any(region.endswith("left") for region in regions)
    has_right = any(region.endswith("right") for region in regions)
    has_top = any(region.startswith("top-") for region in regions)
    has_bottom = any(region.startswith("bottom-") for region in regions)

    clamp = AxisClamp()
    if has_right and not has_left and max_x is not None:
        clamp.x_range = (x_baseline, max_x)
    elif has_left and not has_right and min_x is not None:
        clamp.x_range = (min_x, x_baseline)

    if has_top and not has_bottom and max_y is not None:
        clamp.y_range = (y_baseline, max_y)
    elif has_bottom and not has_top and min_y is not None:
        clamp.y_range = (min_y, y_baseline)

    return clamp


def finite_min_max(values: np.ndarray) -> tuple[float | None, float | None]:
    if values.size == 0:
        return None, None
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None, None
    return float(np.min(finite)), float(np.max(finite))
