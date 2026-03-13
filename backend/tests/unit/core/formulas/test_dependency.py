"""
Unit tests for src/core/formulas/dependency.py

Tests topological sort of derived columns with dependency resolution.
"""

import pytest
from src.core.formulas.dependency import (
    CycleError,
    DerivedColumnDef,
    extract_references,
    resolve_formula_order,
)


class TestExtractReferences:
    """Tests for extract_references function."""

    def test_single_reference(self):
        assert extract_references("[Load]") == ["Load"]

    def test_multiple_references(self):
        refs = extract_references("[Load] / [Area]")
        assert refs == ["Load", "Area"]

    def test_no_references(self):
        assert extract_references("42 + 3") == []

    def test_references_with_spaces(self):
        refs = extract_references("[True Stress] * [Tensile Strain]")
        assert refs == ["True Stress", "Tensile Strain"]

    def test_nested_brackets_not_supported(self):
        """Nested brackets produce unexpected results -- not a supported syntax."""
        refs = extract_references("[[inner]]")
        # Regex matches [inner] first, capturing "[inner" (includes leading bracket)
        assert refs == ["[inner"]


class TestResolveFormulaOrder:
    """Tests for resolve_formula_order (topological sort)."""

    def test_empty_list(self):
        result = resolve_formula_order([], ["A", "B"], [])
        assert result == []

    def test_single_column_no_deps(self):
        """Single derived column referencing only originals."""
        cols = [DerivedColumnDef(id="1", name="C", formula="[A] + [B]")]
        result = resolve_formula_order(cols, ["A", "B"], [])
        assert len(result) == 1
        assert result[0].name == "C"

    def test_linear_chain(self):
        """A -> B -> C (linear dependency chain)."""
        cols = [
            DerivedColumnDef(id="1", name="B", formula="[A] * 2"),
            DerivedColumnDef(id="2", name="C", formula="[B] + 1"),
        ]
        result = resolve_formula_order(cols, ["A"], [])
        names = [c.name for c in result]
        assert names.index("B") < names.index("C")

    def test_diamond_dag(self):
        """A -> B, A -> C, B+C -> D (diamond DAG)."""
        cols = [
            DerivedColumnDef(id="1", name="D", formula="[B] + [C]"),
            DerivedColumnDef(id="2", name="B", formula="[A] * 2"),
            DerivedColumnDef(id="3", name="C", formula="[A] * 3"),
        ]
        result = resolve_formula_order(cols, ["A"], [])
        names = [c.name for c in result]
        assert names.index("B") < names.index("D")
        assert names.index("C") < names.index("D")

    def test_cycle_raises_error(self):
        """Circular dependency should raise CycleError."""
        cols = [
            DerivedColumnDef(id="1", name="X", formula="[Y] + 1"),
            DerivedColumnDef(id="2", name="Y", formula="[X] + 1"),
        ]
        with pytest.raises(CycleError):
            resolve_formula_order(cols, ["A"], [])

    def test_self_reference_raises_error(self):
        """Self-referencing column should raise CycleError."""
        cols = [
            DerivedColumnDef(id="1", name="X", formula="[X] + 1"),
        ]
        with pytest.raises(CycleError):
            resolve_formula_order(cols, ["A"], [])

    def test_disabled_columns_excluded(self):
        """Disabled columns should not appear in output."""
        cols = [
            DerivedColumnDef(id="1", name="B", formula="[A] * 2", enabled=True),
            DerivedColumnDef(id="2", name="C", formula="[A] * 3", enabled=False),
        ]
        result = resolve_formula_order(cols, ["A"], [])
        assert len(result) == 1
        assert result[0].name == "B"

    def test_parameters_not_treated_as_dependencies(self):
        """Parameter references should not create dependency edges."""
        cols = [
            DerivedColumnDef(id="1", name="Stress", formula="[Load] / [width]"),
        ]
        result = resolve_formula_order(cols, ["Load"], ["width"])
        assert len(result) == 1
        assert result[0].name == "Stress"

    def test_many_independent_columns(self):
        """Multiple independent columns should all be returned."""
        cols = [DerivedColumnDef(id=str(i), name=f"D{i}", formula=f"[A] * {i}") for i in range(20)]
        result = resolve_formula_order(cols, ["A"], [])
        assert len(result) == 20

    def test_three_node_cycle(self):
        """Three-node cycle should be detected."""
        cols = [
            DerivedColumnDef(id="1", name="X", formula="[Z] + 1"),
            DerivedColumnDef(id="2", name="Y", formula="[X] + 1"),
            DerivedColumnDef(id="3", name="Z", formula="[Y] + 1"),
        ]
        with pytest.raises(CycleError):
            resolve_formula_order(cols, ["A"], [])
