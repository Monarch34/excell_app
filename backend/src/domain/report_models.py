"""
Shared domain models for report generation.

These DTOs are used across services (chart_metrics, report_compiler)
and output layers (xlsx_report_builder). Keeping them in a shared
domain module prevents inverted dependencies between those layers.
"""

from dataclasses import dataclass


@dataclass
class DerivedColumnSpec:
    """Spec for a derived column in the report."""

    name: str
    formula: str
    unit: str = ""
    description: str = ""
    dependencies: str = ""
    enabled: bool = True


@dataclass
class AnalysisMetricSpec:
    """Spec for an analysis metric in the report."""

    chart_id: str
    chart_title: str
    name: str
    value: float
    unit: str = ""
    x_column: str = ""
    y_column: str = ""


@dataclass
class ParameterSpec:
    """Spec for a parameter in the report."""

    name: str
    value: float
    unit: str = ""
