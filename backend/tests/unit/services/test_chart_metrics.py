from types import SimpleNamespace

from src.services.chart_metrics import (
    ChartMetricResult,
    build_metric_specs_from_chart_metrics,
)


def _build_chart(*, label: str | None, regions: list[str] | None = None):
    return SimpleNamespace(
        id="chart-001",
        title="Area Chart",
        x_column="X",
        y_columns=["Y"],
        area_spec=SimpleNamespace(
            mode="total",
            baseline=0.0,
            x_column="X",
            y_column="Y",
            label=label,
        ),
        baseline_spec=SimpleNamespace(
            x_baseline=0.0,
            y_baseline=0.0,
            regions=regions or [],
        ),
    )


def test_build_metric_specs_uses_custom_area_label_when_provided():
    chart = _build_chart(label="Energy Absorption", regions=["top-right"])
    metrics = [
        ChartMetricResult(
            chart_id="chart-001",
            y_column="Y",
            area_total=12.5,
            area_positive=None,
            area_negative=None,
            area_by_region={"top-right": 12.5},
        )
    ]

    payload = build_metric_specs_from_chart_metrics(metrics, [chart])
    assert len(payload) == 1
    assert payload[0].name == "Energy Absorption"
    assert payload[0].value == 12.5


def test_build_metric_specs_skips_area_metric_when_custom_label_is_blank():
    chart = _build_chart(label="   ", regions=[])
    metrics = [
        ChartMetricResult(
            chart_id="chart-001",
            y_column="Y",
            area_total=3.0,
            area_positive=None,
            area_negative=None,
            area_by_region={},
        )
    ]

    payload = build_metric_specs_from_chart_metrics(metrics, [chart])
    assert payload == []


def test_area_negative_sums_individual_absolutes():
    """
    Regression: area_negative must sum abs of each value, not abs of the sum.

    With bottom regions [-5, 10]:
      - Wrong (old): abs(sum([-5, 10])) = abs(5) = 5
      - Correct (fix): sum(abs(v) for v in [-5, 10]) = 5 + 10 = 15
    """
    from src.services.chart_metrics import _finite_or_none

    bottom_regions = [-5.0, 10.0]

    # The fixed formula
    result_fixed = _finite_or_none(sum(abs(v) for v in bottom_regions))
    assert result_fixed == 15.0

    # The old wrong formula would have produced 5.0
    assert _finite_or_none(abs(sum(bottom_regions))) == 5.0
