"""
Unit tests for src/core/calculations.py

Tests trapezoidal integration, area calculations (total, positive, negative),
and region-based area calculations.
"""

import numpy as np
import pytest

from src.core.calculations import (
    calculate_area,
    calculate_negative_area,
    calculate_positive_area,
    calculate_region_area,
    calculate_total_area,
    filter_nan,
    trapezoidal_integral,
)


class TestTrapezoidalIntegral:
    def test_simple_rectangle(self):
        x = np.array([0.0, 1.0])
        y = np.array([2.0, 2.0])
        assert trapezoidal_integral(x, y) == pytest.approx(2.0)

    def test_simple_triangle(self):
        x = np.array([0.0, 1.0])
        y = np.array([0.0, 2.0])
        assert trapezoidal_integral(x, y) == pytest.approx(1.0)

    def test_empty_arrays(self):
        assert trapezoidal_integral(np.array([]), np.array([])) == 0.0

    def test_single_element(self):
        assert trapezoidal_integral(np.array([1.0]), np.array([5.0])) == 0.0

    def test_mismatched_lengths(self):
        assert trapezoidal_integral(np.array([1.0, 2.0]), np.array([1.0])) == 0.0

    def test_known_integral(self):
        x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
        y = np.array([0.0, 1.0, 4.0, 9.0, 16.0])
        result = trapezoidal_integral(x, y)
        assert result == pytest.approx(22.0)


class TestFilterNan:
    def test_all_valid(self):
        x, y = filter_nan(np.array([1, 2, 3]), np.array([4, 5, 6]))
        assert len(x) == 3

    def test_nan_in_x(self):
        x, y = filter_nan(np.array([1, np.nan, 3]), np.array([4, 5, 6]))
        assert len(x) == 2
        assert list(x) == [1.0, 3.0]
        assert list(y) == [4.0, 6.0]

    def test_nan_in_y(self):
        x, y = filter_nan(np.array([1, 2, 3]), np.array([4, np.nan, 6]))
        assert len(x) == 2

    def test_inf_filtered(self):
        x, y = filter_nan(np.array([1, np.inf, 3]), np.array([4, 5, 6]))
        assert len(x) == 2

    def test_all_nan(self):
        x, y = filter_nan(np.array([np.nan, np.nan]), np.array([np.nan, np.nan]))
        assert len(x) == 0


class TestCalculateTotalArea:
    def test_rectangle_above_zero(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([5.0, 5.0, 5.0])
        assert calculate_total_area(x, y) == pytest.approx(10.0)

    def test_with_baseline(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([5.0, 5.0, 5.0])
        assert calculate_total_area(x, y, baseline=3.0) == pytest.approx(4.0)

    def test_below_baseline_gives_negative(self):
        x = np.array([0.0, 1.0])
        y = np.array([0.0, 0.0])
        assert calculate_total_area(x, y, baseline=5.0) == pytest.approx(-5.0)

    def test_single_point_returns_zero(self):
        assert calculate_total_area(np.array([1.0]), np.array([5.0])) == 0.0

    def test_all_nan_returns_zero(self):
        x = np.array([np.nan, np.nan])
        y = np.array([1.0, 2.0])
        assert calculate_total_area(x, y) == 0.0


class TestCalculatePositiveArea:
    def test_all_positive(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([3.0, 3.0, 3.0])
        assert calculate_positive_area(x, y) == pytest.approx(6.0)

    def test_all_negative_returns_zero(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([-3.0, -3.0, -3.0])
        assert calculate_positive_area(x, y) == 0.0

    def test_mixed_values(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([-1.0, 2.0, -1.0])
        result = calculate_positive_area(x, y)
        assert result > 0


class TestCalculateNegativeArea:
    def test_all_negative(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([-3.0, -3.0, -3.0])
        result = calculate_negative_area(x, y)
        assert result == pytest.approx(6.0)
        assert result > 0

    def test_all_positive_returns_zero(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([3.0, 3.0, 3.0])
        assert calculate_negative_area(x, y) == 0.0


class TestCalculateArea:
    def test_total_mode(self):
        x = np.array([0.0, 1.0])
        y = np.array([2.0, 2.0])
        assert calculate_area(x, y, "total") == pytest.approx(2.0)

    def test_positive_mode(self):
        x = np.array([0.0, 1.0])
        y = np.array([2.0, 2.0])
        assert calculate_area(x, y, "positive") == pytest.approx(2.0)

    def test_negative_mode(self):
        x = np.array([0.0, 1.0])
        y = np.array([-2.0, -2.0])
        assert calculate_area(x, y, "negative") == pytest.approx(2.0)

    def test_unknown_mode_returns_zero(self):
        x = np.array([0.0, 1.0])
        y = np.array([2.0, 2.0])
        assert calculate_area(x, y, "invalid") == 0.0


class TestCalculateRegionArea:
    @pytest.fixture()
    def grid_data(self):
        x = np.array([-2, -1, 0, 1, 2], dtype=float)
        y = np.array([-2, -1, 0, 1, 2], dtype=float)
        return x, y

    def test_top_right(self, grid_data):
        x, y = grid_data
        result = calculate_region_area(x, y, 0, 0, "top-right")
        assert result > 0

    def test_bottom_left(self, grid_data):
        x, y = grid_data
        result = calculate_region_area(x, y, 0, 0, "bottom-left")
        assert result != 0

    def test_unknown_region_returns_zero(self, grid_data):
        x, y = grid_data
        assert calculate_region_area(x, y, 0, 0, "center") == 0.0

    def test_no_points_in_region(self):
        x = np.array([10.0, 20.0])
        y = np.array([10.0, 20.0])
        assert calculate_region_area(x, y, 100, 100, "top-right") == 0.0

    def test_single_point_in_region_returns_zero(self):
        x = np.array([5.0])
        y = np.array([5.0])
        assert calculate_region_area(x, y, 0, 0, "top-right") == 0.0

    def test_boundary_points_included(self):
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([0.0, 1.0, 2.0])
        result = calculate_region_area(x, y, 0, 0, "top-right")
        assert result >= 0

    def test_all_nan_returns_zero(self):
        x = np.array([np.nan, np.nan])
        y = np.array([np.nan, np.nan])
        assert calculate_region_area(x, y, 0, 0, "top-right") == 0.0
