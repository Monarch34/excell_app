"""
Backend architecture boundary checks.

Enforces a simple layering policy:
- src/core must not depend on src/api or src/services.
- src/services must not depend on src/api.

Usage:
    python scripts/check_backend_boundaries.py
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def _iter_py_files(base: Path) -> Iterable[Path]:
    for path in base.rglob("*.py"):
        # Skip virtual environments or hidden cache folders if accidentally nested.
        if "__pycache__" in path.parts:
            continue
        yield path


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def _is_type_checking_block(node: ast.If) -> bool:
    """Return True if this `if` node is an `if TYPE_CHECKING:` guard."""
    test = node.test
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
    )


def _extract_imports(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    imports: list[str] = []

    class _ImportCollector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.in_type_checking_block = 0

        def visit_If(self, node: ast.If) -> None:
            is_type_checking = _is_type_checking_block(node)
            if is_type_checking:
                self.in_type_checking_block += 1
                for child in node.body:
                    self.visit(child)
                self.in_type_checking_block -= 1
                for child in node.orelse:
                    self.visit(child)
                return
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            if self.in_type_checking_block:
                return
            for alias in node.names:
                imports.append(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if self.in_type_checking_block:
                return
            if node.level == 0 and node.module:
                imports.append(node.module)

    _ImportCollector().visit(tree)
    return imports


def _violates(module: str, imported: str) -> str | None:
    if module.startswith("src.core.") or module == "src.core":
        if imported == "src.api" or imported.startswith("src.api."):
            return "src/core cannot import src/api"
        if imported == "src.services" or imported.startswith("src.services."):
            return "src/core cannot import src/services"

    if module.startswith("src.services.") or module == "src.services":
        if imported == "src.api" or imported.startswith("src.api."):
            return "src/services cannot import src/api"

    return None


def main() -> int:
    errors: list[str] = []

    for path in _iter_py_files(SRC):
        module = _module_name(path)
        for imported in _extract_imports(path):
            rule_error = _violates(module, imported)
            if rule_error:
                rel = path.relative_to(ROOT)
                errors.append(f"{rel}: {rule_error} (found import '{imported}')")

    if errors:
        print("Backend boundary violations found:\n")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Backend boundary checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
