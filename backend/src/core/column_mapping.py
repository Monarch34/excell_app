from __future__ import annotations

from typing import Any


def resolve_operation_columns(
    config: dict[str, Any],
    column_mapping: dict[str, str] | None,
) -> dict[str, Any]:
    """Resolve logical role names in operation config to concrete column names."""
    if not column_mapping:
        return config

    resolved = dict(config)
    if "column" in resolved and resolved["column"] in column_mapping:
        resolved["column"] = column_mapping[resolved["column"]]

    if "columns" in resolved and isinstance(resolved["columns"], list):
        resolved_columns: list[dict[str, Any]] = []
        for spec in resolved["columns"]:
            new_spec = dict(spec)
            if new_spec.get("source") in column_mapping:
                new_spec["source"] = column_mapping[new_spec["source"]]
            resolved_columns.append(new_spec)
        resolved["columns"] = resolved_columns

    return resolved
