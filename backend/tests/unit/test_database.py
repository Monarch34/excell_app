"""
Unit tests for src.core.database
"""

import os
import sqlite3

import pytest
import src.core.database as db_module
from src.core.database import init_db, save_config


class TestDatabasePath:
    def test_db_path_is_absolute_when_env_unset(self, monkeypatch):
        """When ANALYSIS_DB_PATH is not set, DB_PATH must be an absolute path."""
        monkeypatch.delenv("ANALYSIS_DB_PATH", raising=False)
        # Reload the module-level constant derived from __file__
        import importlib

        importlib.reload(db_module)
        assert os.path.isabs(
            db_module.DB_PATH
        ), f"DB_PATH should be absolute, got: {db_module.DB_PATH}"

    def test_db_path_respects_env_override(self, monkeypatch, tmp_path):
        custom = str(tmp_path / "custom.db")
        monkeypatch.setenv("ANALYSIS_DB_PATH", custom)
        import importlib

        importlib.reload(db_module)
        assert db_module.DB_PATH == custom


class TestDatabaseIndex:
    def test_domain_index_created_on_init(self, tmp_path, monkeypatch):
        """init_db() must create idx_configs_domain for fast domain-filtered queries."""
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        init_db()

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA index_list(analysis_configs)")
            indexes = [row[1] for row in cursor.fetchall()]
        finally:
            conn.close()

        assert "idx_configs_domain" in indexes

    def test_init_db_is_idempotent(self, tmp_path, monkeypatch):
        """Calling init_db() twice must not raise (IF NOT EXISTS guards)."""
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        init_db()
        init_db()  # second call must not raise


class TestSaveConfigUpsert:
    def test_save_config_upsert(self, tmp_path, monkeypatch):
        """Saving config with same name+domain should update, not duplicate."""
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        init_db()

        save_config("cfg", "domain1", {"v": 1})
        save_config("cfg", "domain1", {"v": 2})

        # Should return same row (upsert)
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM analysis_configs WHERE name='cfg' AND domain='domain1'"
            )
            count = cursor.fetchone()[0]
        finally:
            conn.close()

        assert count == 1, "Upsert should not create duplicate rows"

    def test_different_domains_create_separate_rows(self, tmp_path, monkeypatch):
        """Same name but different domain should create separate rows."""
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr(db_module, "DB_PATH", db_path)
        init_db()

        save_config("cfg", "domain1", {"v": 1})
        save_config("cfg", "domain2", {"v": 2})

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM analysis_configs WHERE name='cfg'")
            count = cursor.fetchone()[0]
        finally:
            conn.close()

        assert count == 2


class TestMigrationAddsUniqueConstraint:
    def test_migration_adds_unique_constraint(self, tmp_path, monkeypatch):
        """Migration should add UNIQUE(name, domain) to legacy tables."""
        db_path = str(tmp_path / "test.db")
        monkeypatch.setattr(db_module, "DB_PATH", db_path)

        # Create legacy table WITHOUT unique constraint
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE analysis_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                domain TEXT NOT NULL,
                config_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_configs_domain ON analysis_configs(domain)")
        conn.commit()
        conn.close()

        # init_db should migrate
        init_db()

        # Verify unique constraint exists by trying to insert duplicates
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                "INSERT INTO analysis_configs (name, domain, config_data, created_at, updated_at) VALUES ('a','b','{}','now','now')"
            )
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO analysis_configs (name, domain, config_data, created_at, updated_at) VALUES ('a','b','{}','now','now')"
                )
        finally:
            conn.close()
