"""
Sync backend OpenAPI contract to frontend generated TypeScript types.

Outputs:
- docs/openapi.json
- frontend/src/types/generated/openapi.ts

Usage:
    .\\venv\\Scripts\\python.exe scripts\\sync_api_contract.py
    .\\venv\\Scripts\\python.exe scripts\\sync_api_contract.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
OPENAPI_PATH = REPO_ROOT / "docs" / "openapi.json"
TYPES_PATH = REPO_ROOT / "frontend" / "src" / "types" / "generated" / "openapi.ts"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ref_name(ref: str) -> str:
    return ref.split("/")[-1]


def _is_identifier(name: str) -> bool:
    return bool(IDENT_RE.match(name))


def _quote_prop(name: str) -> str:
    return name if _is_identifier(name) else json.dumps(name)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _maybe_parenthesize_for_array(type_str: str) -> str:
    if "|" in type_str or "&" in type_str:
        return f"({type_str})"
    return type_str


def _schema_to_ts(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return _ref_name(str(schema["$ref"]))

    if "const" in schema:
        return json.dumps(schema["const"])

    if "enum" in schema and isinstance(schema["enum"], list):
        enum_values = [json.dumps(value) for value in schema["enum"]]
        return " | ".join(enum_values) if enum_values else "unknown"

    for key, op in (("anyOf", " | "), ("oneOf", " | "), ("allOf", " & ")):
        members = schema.get(key)
        if isinstance(members, list) and members:
            ts_members = [_schema_to_ts(member) for member in members]
            union = op.join(_dedupe(ts_members))
            return union if union else "unknown"

    schema_type = schema.get("type")

    if schema_type == "array":
        item_type = _schema_to_ts(schema.get("items", {}))
        return f"{_maybe_parenthesize_for_array(item_type)}[]"

    if schema_type == "object" or "properties" in schema or "additionalProperties" in schema:
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        additional = schema.get("additionalProperties", None)

        if isinstance(properties, dict) and properties:
            parts: list[str] = []
            for prop_name, prop_schema in sorted(properties.items()):
                optional = "" if prop_name in required else "?"
                parts.append(f"{_quote_prop(prop_name)}{optional}: {_schema_to_ts(prop_schema)}")
            if additional is True:
                parts.append("[key: string]: unknown")
            elif isinstance(additional, dict):
                parts.append(f"[key: string]: {_schema_to_ts(additional)}")
            return "{ " + "; ".join(parts) + " }"

        if additional is True:
            return "Record<string, unknown>"
        if isinstance(additional, dict):
            return f"Record<string, {_schema_to_ts(additional)}>"
        return "Record<string, unknown>"

    primitive_map = {
        "string": "string",
        "number": "number",
        "integer": "number",
        "boolean": "boolean",
        "null": "null",
    }
    ts_type = primitive_map.get(str(schema_type), "unknown")
    if schema.get("nullable") and "null" not in ts_type:
        return f"{ts_type} | null"
    return ts_type


def _emit_schema(name: str, schema: dict[str, Any]) -> str:
    is_object = (
        schema.get("type") == "object"
        or "properties" in schema
        or ("additionalProperties" in schema and "enum" not in schema)
    )
    if is_object:
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        additional = schema.get("additionalProperties", None)

        lines = [f"export interface {name} {{"]
        if isinstance(properties, dict):
            for prop_name, prop_schema in sorted(properties.items()):
                optional = "" if prop_name in required else "?"
                lines.append(f"  {_quote_prop(prop_name)}{optional}: {_schema_to_ts(prop_schema)};")

        if additional is True:
            lines.append("  [key: string]: unknown;")
        elif isinstance(additional, dict):
            lines.append(f"  [key: string]: {_schema_to_ts(additional)};")

        if len(lines) == 1:
            lines.append("  [key: string]: unknown;")
        lines.append("}")
        return "\n".join(lines)

    return f"export type {name} = {_schema_to_ts(schema)};"


def _render_types(spec: dict[str, Any]) -> str:
    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        raise ValueError("OpenAPI spec does not contain components.schemas")

    blocks = [
        "// Auto-generated by scripts/sync_api_contract.py. Do not edit manually.",
        "// Source: docs/openapi.json",
        "",
    ]

    for name in sorted(schemas):
        schema = schemas[name]
        if isinstance(schema, dict):
            blocks.append(_emit_schema(name, schema))
            blocks.append("")

    return "\n".join(blocks).rstrip() + "\n"


def _write_if_changed(path: Path, content: str, check_only: bool) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    changed = existing != content
    if changed and not check_only:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return changed


def main() -> int:
    from src.api.server import app

    parser = argparse.ArgumentParser(description="Sync OpenAPI spec and frontend API types.")
    parser.add_argument(
        "--check", action="store_true", help="Fail if generated files are out of date."
    )
    args = parser.parse_args()

    spec = app.openapi()
    openapi_content = json.dumps(spec, indent=2, sort_keys=True) + "\n"
    types_content = _render_types(spec)

    openapi_changed = _write_if_changed(OPENAPI_PATH, openapi_content, args.check)
    types_changed = _write_if_changed(TYPES_PATH, types_content, args.check)

    if args.check:
        if openapi_changed or types_changed:
            print("API contract files are out of date. Run:")
            print("  .\\venv\\Scripts\\python.exe scripts\\sync_api_contract.py")
            return 1
        print("API contract files are up to date.")
        return 0

    print(f"Wrote {OPENAPI_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {TYPES_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
