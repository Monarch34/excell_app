"""
Seed the database with extra configs for testing the config library card/list UI.

Usage (from repo root):
    python backend/scripts/seed_configs.py
Or from backend directory:
    python scripts/seed_configs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.core.database import get_config_by_id, get_configs, init_db, save_config

# Minimal valid config_data (AnalysisConfig-like) if no existing config to copy
MINIMAL_CONFIG = {
    "version": "1",
    "name": "Seed",
    "description": "",
    "selectedColumns": [],
    "parameters": [],
    "derivedColumns": [],
    "charts": [],
    "columnOrder": [],
    "parameterOrder": [],
    "separators": [],
    "createdAt": "2025-01-01T00:00:00",
    "updatedAt": "2025-01-01T00:00:00",
}

NAMES = [
    "Test Config Alpha",
    "Test Config Beta",
    "Test Config Gamma",
    "Test Config Delta",
]


def main() -> None:
    init_db()
    configs = get_configs()
    # Use first existing config's payload if any, else minimal
    if configs:
        first_id = configs[0]["id"]
        existing = get_config_by_id(first_id)
        config_data = existing["config_data"] if existing else MINIMAL_CONFIG
    else:
        config_data = MINIMAL_CONFIG

    for name in NAMES:
        save_config(name, "", config_data)
        print(f"Saved: {name}")

    print("Done. 4 configs added.")


if __name__ == "__main__":
    main()
