import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("ANALYSIS_DB_PATH", str(Path(__file__).parent.parent / "analysis_app.db"))


def _migrate_unique_constraint(conn: sqlite3.Connection) -> None:
    """Recreate analysis_configs table with UNIQUE(name, domain) if missing."""
    cursor = conn.cursor()
    # Check if the unique constraint already exists
    cursor.execute("PRAGMA index_list(analysis_configs)")
    for row in cursor.fetchall():
        index_name = row[1]
        unique = row[2]
        if unique:
            cursor.execute(f"PRAGMA index_info({index_name})")
            cols = [r[2] for r in cursor.fetchall()]
            if cols == ["name", "domain"]:
                return  # constraint already present

    # SQLite cannot ALTER ADD CONSTRAINT — recreate the table
    cursor.execute("ALTER TABLE analysis_configs RENAME TO _configs_old")
    cursor.execute("""
    CREATE TABLE analysis_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        config_data TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(name, domain)
    )
    """)
    # Use a transaction for the data copy + old table drop so a crash
    # leaves _configs_old intact for recovery on next startup.
    with conn:
        cursor.execute("""
        INSERT OR IGNORE INTO analysis_configs
            (id, name, domain, config_data, created_at, updated_at)
        SELECT id, name, domain, config_data, created_at, updated_at
        FROM _configs_old
        """)
        cursor.execute("DROP TABLE _configs_old")


def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.OperationalError as exc:
        logger.error("Failed to connect to database at %s: %s", DB_PATH, exc)
        raise RuntimeError(f"Cannot open database at {DB_PATH}: {exc}") from exc
    try:
        cursor = conn.cursor()

        # Recover from a previous crash that left _configs_old behind.
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_configs_old'")
        if cursor.fetchone():
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_configs'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE _configs_old")
            else:
                cursor.execute("ALTER TABLE _configs_old RENAME TO analysis_configs")
            conn.commit()
            logger.info("Recovered from interrupted migration (_configs_old)")

        cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        domain TEXT NOT NULL,
        config_data TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(name, domain)
    )
    """)
        cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_configs_domain
    ON analysis_configs(domain)
    """)
        conn.commit()
        _migrate_unique_constraint(conn)
    finally:
        conn.close()


def save_config(name: str, domain: str, config_data: dict[str, Any]) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
    INSERT INTO analysis_configs (name, domain, config_data, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(name, domain) DO UPDATE SET
        config_data = excluded.config_data,
        updated_at = excluded.updated_at
    """,
            (name, domain, json.dumps(config_data), now, now),
        )
        conn.commit()

        # lastrowid may be 0 on UPSERT update path; fetch the true ID
        config_id = cursor.lastrowid
        if not config_id:
            cursor.execute(
                "SELECT id FROM analysis_configs WHERE name = ? AND domain = ?",
                (name, domain),
            )
            row = cursor.fetchone()
            config_id = row[0] if row else 0

        return config_id
    finally:
        conn.close()


def get_configs(domain: str | None = None) -> list[dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if domain:
            cursor.execute(
                "SELECT id, name, domain, created_at, updated_at FROM analysis_configs WHERE domain = ?",
                (domain,),
            )
        else:
            cursor.execute("SELECT id, name, domain, created_at, updated_at FROM analysis_configs")

        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_config_by_id(config_id: int) -> dict[str, Any] | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_configs WHERE id = ?", (config_id,))
        row = cursor.fetchone()

        if row:
            data = dict(row)
            try:
                parsed = json.loads(data["config_data"])
                data["config_data"] = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                logger.warning("Corrupt config_data for config id=%s", config_id)
                data["config_data"] = {}
            return data
        return None
    finally:
        conn.close()


def delete_config(config_id: int):
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analysis_configs WHERE id = ?", (config_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"Configuration with id {config_id} not found")
        conn.commit()
    finally:
        conn.close()
