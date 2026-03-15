"""
Integration tests for the configs router.

Covers GET/POST/DELETE for /api/v3/configs and /api/v3/configs/limits.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_configs.db")
    monkeypatch.setattr("src.core.database.DB_PATH", db_path)
    app = create_app()
    with TestClient(app) as c:
        yield c


SAMPLE_CONFIG = {
    "name": "My Config",
    "domain": "testing",
    "config_data": {"columns": ["A", "B"], "formulas": []},
}


class TestGetLimits:
    def test_limits_returns_200(self, client):
        resp = client.get("/api/v3/configs/limits")
        assert resp.status_code == 200

    def test_limits_response_shape(self, client):
        body = client.get("/api/v3/configs/limits").json()
        assert "max_derived_columns" in body
        assert "max_file_size_mb" in body
        assert isinstance(body["max_derived_columns"], int)
        assert isinstance(body["max_file_size_mb"], int)


class TestCreateConfig:
    def test_create_returns_201_shape(self, client):
        resp = client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["id"], int)

    def test_upsert_same_name_and_domain(self, client):
        resp1 = client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        id1 = resp1.json()["id"]
        resp2 = client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        id2 = resp2.json()["id"]
        assert id1 == id2

    def test_missing_name_returns_422(self, client):
        resp = client.post("/api/v3/configs", json={"domain": "x", "config_data": {}})
        assert resp.status_code == 422

    def test_empty_name_returns_422(self, client):
        resp = client.post("/api/v3/configs", json={"name": "", "domain": "", "config_data": {}})
        assert resp.status_code == 422

    def test_missing_config_data_returns_422(self, client):
        resp = client.post("/api/v3/configs", json={"name": "x"})
        assert resp.status_code == 422

    def test_oversized_config_data_returns_422(self, client):
        huge = {"big_key": "x" * (6 * 1024 * 1024)}
        resp = client.post(
            "/api/v3/configs",
            json={"name": "big", "domain": "", "config_data": huge},
        )
        assert resp.status_code == 422


class TestListConfigs:
    def test_list_empty_returns_200(self, client):
        resp = client.get("/api/v3/configs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_after_create(self, client):
        client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        resp = client.get("/api/v3/configs")
        assert resp.status_code == 200
        configs = resp.json()
        assert len(configs) == 1
        assert configs[0]["name"] == "My Config"
        assert configs[0]["domain"] == "testing"

    def test_list_filter_by_domain(self, client):
        client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        client.post(
            "/api/v3/configs",
            json={"name": "Other", "domain": "other_domain", "config_data": {}},
        )
        resp = client.get("/api/v3/configs", params={"domain": "testing"})
        configs = resp.json()
        assert len(configs) == 1
        assert configs[0]["domain"] == "testing"

    def test_list_response_shape(self, client):
        client.post("/api/v3/configs", json=SAMPLE_CONFIG)
        item = client.get("/api/v3/configs").json()[0]
        assert "id" in item
        assert "name" in item
        assert "domain" in item
        assert "created_at" in item
        assert "updated_at" in item
        assert "config_data" not in item


class TestFetchConfig:
    def test_fetch_existing_returns_200(self, client):
        config_id = client.post("/api/v3/configs", json=SAMPLE_CONFIG).json()["id"]
        resp = client.get(f"/api/v3/configs/{config_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "My Config"
        assert body["config_data"] == {"columns": ["A", "B"], "formulas": []}

    def test_fetch_nonexistent_returns_404(self, client):
        resp = client.get("/api/v3/configs/99999")
        assert resp.status_code == 404

    def test_fetch_invalid_id_returns_422(self, client):
        resp = client.get("/api/v3/configs/0")
        assert resp.status_code == 422

    def test_fetch_negative_id_returns_422(self, client):
        resp = client.get("/api/v3/configs/-1")
        assert resp.status_code == 422


class TestDeleteConfig:
    def test_delete_existing_returns_200(self, client):
        config_id = client.post("/api/v3/configs", json=SAMPLE_CONFIG).json()["id"]
        resp = client.delete(f"/api/v3/configs/{config_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_delete_removes_from_list(self, client):
        config_id = client.post("/api/v3/configs", json=SAMPLE_CONFIG).json()["id"]
        client.delete(f"/api/v3/configs/{config_id}")
        configs = client.get("/api/v3/configs").json()
        assert len(configs) == 0

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/v3/configs/99999")
        assert resp.status_code == 404

    def test_delete_invalid_id_returns_422(self, client):
        resp = client.delete("/api/v3/configs/0")
        assert resp.status_code == 422

    def test_double_delete_returns_404(self, client):
        config_id = client.post("/api/v3/configs", json=SAMPLE_CONFIG).json()["id"]
        client.delete(f"/api/v3/configs/{config_id}")
        resp = client.delete(f"/api/v3/configs/{config_id}")
        assert resp.status_code == 404
