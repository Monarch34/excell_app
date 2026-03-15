"""
Repository abstraction over the configs persistence layer.

Wraps the raw ``core.database`` functions so that routers depend on
an injectable interface rather than bare module-level functions.
Tests can substitute ``InMemoryConfigRepository`` or mock the class.
"""

from __future__ import annotations

from typing import Any

from src.core.database import (
    delete_config as _db_delete,
    get_config_by_id as _db_get_by_id,
    get_configs as _db_list,
    save_config as _db_save,
)


class ConfigRepository:
    """Thin repository over the SQLite config store."""

    def save(self, name: str, domain: str, config_data: dict[str, Any]) -> int:
        return _db_save(name, domain, config_data)

    def list(self, domain: str | None = None) -> list[dict[str, Any]]:
        return _db_list(domain)

    def get_by_id(self, config_id: int) -> dict[str, Any] | None:
        return _db_get_by_id(config_id)

    def delete(self, config_id: int) -> None:
        _db_delete(config_id)
