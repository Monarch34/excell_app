"""
Dependency resolution for derived columns using topological sort.

Implements Kahn's algorithm (BFS topological sort) to determine
the correct evaluation order for derived columns that may reference
each other.
"""

import logging
import re
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)

COLUMN_REF_PATTERN = re.compile(r"\[([^\]]+)\]")


class CycleError(Exception):
    """Raised when circular dependencies are detected among derived columns."""

    def __init__(self, cycle_path: list[str]):
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"Circular dependency detected: {cycle_str}")


@dataclass
class DerivedColumnDef:
    """Minimal derived column definition for dependency resolution."""

    id: str
    name: str
    formula: str
    enabled: bool = True


def extract_references(formula: str) -> list[str]:
    """Extract all [Column Name] references from a formula string."""
    return COLUMN_REF_PATTERN.findall(formula)


def resolve_formula_order(
    derived_columns: list[DerivedColumnDef],
    available_originals: list[str],
    parameters: list[str],
) -> list[DerivedColumnDef]:
    """
    Determine evaluation order for derived columns via topological sort.

    Uses Kahn's algorithm (BFS-based topological sort) to resolve
    dependencies between derived columns. Columns may reference
    original dataset columns, parameters, and other derived columns.

    Args:
        derived_columns: List of derived column definitions to sort.
        available_originals: Names of original dataset columns.
        parameters: Names of available parameters.

    Returns:
        List of DerivedColumnDef in correct evaluation order.

    Raises:
        CycleError: If circular dependencies are detected, with the cycle path.
    """
    if not derived_columns:
        return []

    # Filter to enabled columns only
    active = [dc for dc in derived_columns if dc.enabled]
    if not active:
        return []

    # Build sets for quick lookup
    derived_names: dict[str, DerivedColumnDef] = {dc.name: dc for dc in active}

    # Build adjacency list: edges from dependency -> dependent
    # in_degree[col_name] = number of derived columns it depends on
    in_degree: dict[str, int] = {dc.name: 0 for dc in active}
    dependents: dict[str, list[str]] = {dc.name: [] for dc in active}

    for dc in active:
        refs = extract_references(dc.formula)
        for ref in refs:
            if ref in derived_names and ref != dc.name:
                # This derived column depends on another derived column
                in_degree[dc.name] += 1
                dependents[ref].append(dc.name)
            elif ref == dc.name:
                # Self-reference is a cycle
                raise CycleError([dc.name, dc.name])
            # References to originals/parameters have no dependency edge

    # Kahn's algorithm
    queue: deque[str] = deque(name for name, deg in in_degree.items() if deg == 0)
    sorted_names: list[str] = []

    while queue:
        current = queue.popleft()
        sorted_names.append(current)

        for dep in dependents.get(current, []):
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    # Check for cycles
    if len(sorted_names) < len(active):
        # Find the cycle for error reporting
        remaining = set(in_degree.keys()) - set(sorted_names)
        cycle_path = _trace_cycle(remaining, active, derived_names)
        raise CycleError(cycle_path)

    # Return in sorted order
    return [derived_names[name] for name in sorted_names]


def _trace_cycle(
    remaining: set[str],
    active: list[DerivedColumnDef],
    derived_names: dict[str, DerivedColumnDef],
) -> list[str]:
    """Trace a cycle path through remaining nodes for error reporting."""
    if not remaining:
        return []

    start = next(iter(remaining))
    path = [start]
    visited: set[str] = {start}

    current = start
    max_iterations = len(remaining) + 1
    for _ in range(max_iterations):
        dc = derived_names.get(current)
        if dc is None:
            break

        refs = extract_references(dc.formula)
        next_node = None
        for ref in refs:
            if ref in remaining and ref in derived_names:
                if ref in visited:
                    path.append(ref)
                    return path
                next_node = ref
                break

        if next_node is None:
            break

        path.append(next_node)
        visited.add(next_node)
        current = next_node

    path.append(start)
    return path
