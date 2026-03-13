"""
Chart Generator service for creating visualizations.
Generates matplotlib charts for embedding in Excel reports.
"""

import matplotlib

matplotlib.use("Agg")
import io
import logging

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from src.core.charts.filtering import (
    compute_region_axis_clamp,
    filter_series_by_area_mode,
    filter_series_by_regions,
    normalize_regions,
)

from ..utils.constants import CHART_CONFIG

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Service for generating matplotlib charts for analysis.
    Uses generate_from_spec for frontend-driven chart definitions.
    """

    def __init__(self):
        """Initialize chart generator with configuration."""
        self.figsize = CHART_CONFIG["FIGSIZE"]
        self.dpi = CHART_CONFIG["DPI"]
        self.formatter = ticker.FormatStrFormatter("%g")

        logger.debug(f"ChartGenerator initialized: {self.figsize} @ {self.dpi} DPI")

    @staticmethod
    def _apply_region_axis_clamps(
        ax: plt.Axes,
        baseline_regions: list[str],
        x_baseline: float,
        y_baseline: float,
        min_x: float | None,
        max_x: float | None,
        min_y: float | None,
        max_y: float | None,
    ) -> None:
        clamp = compute_region_axis_clamp(
            regions=baseline_regions,
            x_baseline=x_baseline,
            y_baseline=y_baseline,
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
        )
        if clamp.x_range is not None:
            ax.set_xlim(left=clamp.x_range[0], right=clamp.x_range[1])
        if clamp.y_range is not None:
            ax.set_ylim(bottom=clamp.y_range[0], top=clamp.y_range[1])

    def generate_from_spec(
        self,
        df: pd.DataFrame,
        spec: dict,
    ) -> io.BytesIO:
        """
        Generate a chart PNG from a ChartSpec-like dict (from the frontend).

        Args:
            df: DataFrame with data columns
            spec: Dict with keys: title, x_column, y_columns, chart_type,
                  line_color, fill_color, area_spec

        Returns:
            BytesIO buffer containing the PNG image
        """
        logger.debug(f"Generating chart from spec: {spec.get('title', 'Untitled')}")

        x_col = spec.get("x_column", "")
        if x_col not in df.columns:
            raise ValueError(f"X column '{x_col}' not found")

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        try:
            return self._render_chart(fig, ax, df, spec)
        finally:
            plt.close(fig)

    def _render_chart(
        self,
        fig: plt.Figure,
        ax: plt.Axes,
        df: pd.DataFrame,
        spec: dict,
    ) -> io.BytesIO:
        x_col = spec.get("x_column", "")
        y_cols = spec.get("y_columns", [])
        chart_type = spec.get("chart_type", "line")
        title = spec.get("title", "")
        line_color = spec.get("line_color") or CHART_CONFIG.get("DEFAULT_LINE_COLOR", "#2F5597")
        fill_color = spec.get("fill_color") or CHART_CONFIG.get("DEFAULT_FILL_COLOR", "#D5F5E3")
        try:
            line_width = float(spec.get("line_width") or 2.0)
        except (ValueError, TypeError):
            line_width = 2.0
        try:
            marker_size = float(spec.get("marker_size") or 20.0)
        except (ValueError, TypeError):
            marker_size = 20.0
        fill_alpha = spec.get("fill_opacity")
        if fill_alpha is None:
            fill_alpha = CHART_CONFIG.get("DEFAULT_FILL_ALPHA", 0.4)

        area_spec = spec.get("area_spec")
        baseline_spec = spec.get("baseline_spec") or {}
        baseline_regions = normalize_regions(baseline_spec.get("regions") or [])
        x_axis_label = spec.get("x_axis_label")
        y_axis_label = spec.get("y_axis_label")

        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        plotted_x: list[np.ndarray] = []
        plotted_y: list[np.ndarray] = []
        x_baseline = float(baseline_spec.get("x_baseline") or 0.0)
        y_baseline = float(baseline_spec.get("y_baseline") or 0.0)

        plotted_count = 0
        for y_col in y_cols:
            if y_col not in df.columns:
                logger.warning(f"Y column '{y_col}' not found, skipping")
                continue

            x_data = pd.to_numeric(df[x_col], errors="coerce")
            y_data = pd.to_numeric(df[y_col], errors="coerce")
            mask = ~(x_data.isna() | y_data.isna())
            x = x_data[mask]
            y = y_data[mask]

            x, y = filter_series_by_regions(
                x=x,
                y=y,
                regions=baseline_regions,
                x_baseline=x_baseline,
                y_baseline=y_baseline,
            )
            x, y = filter_series_by_area_mode(
                x=x,
                y=y,
                chart_type=chart_type,
                area_spec=area_spec if isinstance(area_spec, dict) else None,
                has_region_filter=len(baseline_regions) > 0,
            )

            if len(x) < 1:
                continue

            x_values = x.to_numpy(dtype=float)
            y_values = y.to_numpy(dtype=float)

            should_fill = chart_type == "area"
            if should_fill and len(x_values) >= 2:
                # Keep area polygons stable/visible in matplotlib.
                order = np.argsort(x_values)
                x_values = x_values[order]
                y_values = y_values[order]

            plotted_x.append(x_values)
            plotted_y.append(y_values)

            label = y_col
            if should_fill and area_spec and isinstance(area_spec, dict) and area_spec.get("label"):
                label = area_spec.get("label")

            if chart_type == "scatter":
                ax.scatter(
                    x_values,
                    y_values,
                    label=label,
                    s=marker_size,
                    alpha=0.75,
                    color=line_color,
                    linewidths=0,
                )
                plotted_count += 1
            elif should_fill:
                if len(x_values) >= 2:
                    ax.plot(
                        x_values,
                        y_values,
                        color=line_color,
                        linewidth=line_width,
                        label=label,
                        antialiased=True,
                    )
                    # Frontend area uses fill-to-zero visual behavior.
                    ax.fill_between(x_values, y_values, 0.0, color=fill_color, alpha=fill_alpha)
                    plotted_count += 1
                else:
                    # Keep highly filtered area chart visible with a marker.
                    ax.scatter(
                        x_values,
                        y_values,
                        label=label,
                        s=max(marker_size, 18.0),
                        alpha=0.85,
                        color=line_color,
                        linewidths=0,
                    )
                    plotted_count += 1
            else:
                if len(x_values) >= 2:
                    ax.plot(
                        x_values,
                        y_values,
                        color=line_color,
                        linewidth=line_width,
                        label=label,
                        antialiased=True,
                    )
                    plotted_count += 1
                else:
                    ax.scatter(
                        x_values,
                        y_values,
                        label=label,
                        s=max(marker_size, 16.0),
                        alpha=0.85,
                        color=line_color,
                        linewidths=0,
                    )
                    plotted_count += 1

        if title:
            ax.set_title(title, fontweight="bold")
        ax.set_xlabel(x_axis_label or x_col)
        if y_cols:
            ax.set_ylabel(y_axis_label or ", ".join(y_cols))

        if baseline_spec:
            x_bline = baseline_spec.get("x_baseline")
            y_bline = baseline_spec.get("y_baseline")
            try:
                if x_bline is not None:
                    ax.axvline(x=float(x_bline), color="#6b7280", linestyle=":", linewidth=1.0)
            except (TypeError, ValueError):
                logger.warning("Invalid x_baseline value: %s", x_bline)
            try:
                if y_bline is not None:
                    ax.axhline(y=float(y_bline), color="#6b7280", linestyle=":", linewidth=1.0)
            except (TypeError, ValueError):
                logger.warning("Invalid y_baseline value: %s", y_bline)

        if plotted_x and plotted_y:
            all_x = np.concatenate(plotted_x)
            all_y = np.concatenate(plotted_y)
            min_x = float(np.min(all_x)) if all_x.size > 0 else None
            max_x = float(np.max(all_x)) if all_x.size > 0 else None
            min_y = float(np.min(all_y)) if all_y.size > 0 else None
            max_y = float(np.max(all_y)) if all_y.size > 0 else None
        else:
            min_x = max_x = min_y = max_y = None

        # Match frontend region axis clamping behavior.
        self._apply_region_axis_clamps(
            ax=ax,
            baseline_regions=baseline_regions,
            x_baseline=x_baseline,
            y_baseline=y_baseline,
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
        )

        # Match frontend area-axis baseline clamping behavior when no explicit regions.
        if chart_type == "area" and isinstance(area_spec, dict) and len(baseline_regions) == 0:
            mode = area_spec.get("mode")
            if mode in ("positive", "negative"):
                baseline = float(area_spec.get("baseline") or 0.0)
                axis = area_spec.get("baseline_axis") or "y"
                if axis == "x":
                    if mode == "positive":
                        ax.set_xlim(left=baseline)
                    else:
                        ax.set_xlim(right=baseline)
                else:
                    if mode == "positive":
                        ax.set_ylim(bottom=baseline)
                    else:
                        ax.set_ylim(top=baseline)

        ax.xaxis.set_major_formatter(self.formatter)
        ax.yaxis.set_major_formatter(self.formatter)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
        ax.tick_params(axis="both", labelsize=9, colors="#334155")
        ax.grid(False)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#94a3b8")
        ax.spines["bottom"].set_color("#94a3b8")

        if plotted_count == 0:
            ax.text(
                0.5,
                0.5,
                "No plottable data after filters",
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=10,
                color="#64748b",
            )

        if len(y_cols) > 1:
            ax.legend(frameon=False, fontsize=9)

        fig.tight_layout(pad=1.1)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self.dpi, facecolor="white")
        buf.seek(0)
        return buf

    def generate_error_placeholder(self, title: str, message: str) -> io.BytesIO:
        """Generate a visible placeholder image when chart rendering fails."""
        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)
        try:
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
            ax.axis("off")
            ax.text(
                0.5,
                0.62,
                title or "Chart",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
                color="#0f172a",
            )
            ax.text(
                0.5,
                0.44,
                "Chart rendering failed",
                ha="center",
                va="center",
                fontsize=10,
                color="#b91c1c",
            )
            safe_message = (message or "").strip()
            if len(safe_message) > 140:
                safe_message = safe_message[:137] + "..."
            ax.text(
                0.5,
                0.30,
                safe_message or "Unknown error",
                ha="center",
                va="center",
                fontsize=9,
                color="#64748b",
            )
            fig.tight_layout(pad=1.2)

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=self.dpi, facecolor="white")
            buf.seek(0)
            return buf
        finally:
            plt.close(fig)
