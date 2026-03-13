"""
HTTP-layer integration tests for the main API endpoints.

Uses FastAPI TestClient across routers, schema validation, and service wiring.
"""

from __future__ import annotations

import csv
import io

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app

MINIMAL_ROWS = [
    {"Time": 0.0, "Load": 0.0, "Extension": 0.0},
    {"Time": 1.0, "Load": 100.0, "Extension": 0.5},
    {"Time": 2.0, "Load": 200.0, "Extension": 1.0},
]


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def upload_dataset_id(client: TestClient, rows: list[dict[str, float]]) -> str:
    if not rows:
        raise ValueError("rows must not be empty")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    response = client.post(
        "/api/v3/datasets/upload",
        files={"file": ("test.csv", output.getvalue(), "text/csv")},
    )
    assert response.status_code == 200
    dataset_id = response.json().get("dataset_id")
    assert isinstance(dataset_id, str) and dataset_id
    return dataset_id


def fetch_run_processed_data(client: TestClient, run_id: str) -> list[dict[str, object]]:
    response = client.get(f"/api/v3/processing/runs/{run_id}/data")
    assert response.status_code == 200
    payload = response.json()
    data = payload.get("processed_data")
    assert isinstance(data, list)
    return data


class TestDatasetUpload:
    def test_upload_accepts_common_filename_symbols(self, client):
        csv_content = "A,B\n1,2\n3,4\n"
        for filename in (
            "@Specimen_RawData_1.3.csv",
            "Specimen RawData (1).csv",
            "Specimen#1.csv",
        ):
            response = client.post(
                "/api/v3/datasets/upload",
                files={"file": (filename, csv_content, "text/csv")},
            )
            assert response.status_code == 200, response.text
            assert response.json().get("filename") == filename

    def test_upload_rejects_path_like_filename(self, client):
        csv_content = "A,B\n1,2\n3,4\n"
        response = client.post(
            "/api/v3/datasets/upload",
            files={"file": ("../secret.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 400
        assert "Invalid filename path" in response.json().get("detail", "")


class TestProcessingRun:
    def test_minimal_request_returns_200(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post("/api/v3/processing/run", json={"dataset_id": dataset_id})
        assert resp.status_code == 200

    def test_response_shape(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/processing/run",
            json={"dataset_id": dataset_id, "project_name": "TestProject"},
        )
        body = resp.json()
        assert isinstance(body.get("processed_data"), list)
        assert len(body["processed_data"]) == len(MINIMAL_ROWS)
        assert "results" in body
        assert "project_name" in body
        assert "run_id" in body
        assert body["project_name"] == "TestProject"
        assert isinstance(body["run_id"], str)
        assert len(body["run_id"]) > 0

    def test_processed_data_row_count(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post("/api/v3/processing/run", json={"dataset_id": dataset_id})
        body = resp.json()
        rows = fetch_run_processed_data(client, body["run_id"])
        assert len(rows) == len(MINIMAL_ROWS)

    def test_user_formula_evaluated(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/processing/run",
            json={
                "dataset_id": dataset_id,
                "user_formulas": [{"name": "DoubleLoad", "formula": "[Load] * 2", "unit": "N"}],
            },
        )
        assert resp.status_code == 200
        rows = fetch_run_processed_data(client, resp.json()["run_id"])
        assert "DoubleLoad" in rows[0]
        assert rows[1]["DoubleLoad"] == pytest.approx(200.0)

    def test_parameters_used_in_formula(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/processing/run",
            json={
                "dataset_id": dataset_id,
                "parameters": {"A0": 20.0},
                "user_formulas": [{"name": "Stress", "formula": "[Load] / [A0]", "unit": "MPa"}],
            },
        )
        assert resp.status_code == 200
        rows = fetch_run_processed_data(client, resp.json()["run_id"])
        assert "Stress" in rows[0]
        assert rows[2]["Stress"] == pytest.approx(10.0)

    def test_processing_preserves_precision_for_ref_offset_formula(self, client):
        rows = [
            {"Load": 0.12345678901234566, "Extension": 0.0},
            {"Load": 0.22345678901234567, "Extension": 0.1},
            {"Load": 0.32345678901234565, "Extension": 0.2},
        ]
        dataset_id = upload_dataset_id(client, rows)
        resp = client.post(
            "/api/v3/processing/run",
            json={
                "dataset_id": dataset_id,
                "initial_results": {"manual_reference_index": 1},
                "user_formulas": [{"name": "New Load", "formula": "[Load] - REF([Load])"}],
            },
        )
        assert resp.status_code == 200
        processed = fetch_run_processed_data(client, resp.json()["run_id"])
        assert processed[0]["New Load"] is None
        assert processed[1]["New Load"] == pytest.approx(0.0, abs=1e-15)
        assert processed[2]["New Load"] == pytest.approx(0.1, abs=1e-15)

    def test_unknown_run_data_returns_404(self, client):
        response = client.get("/api/v3/processing/runs/unknown-run-id/data")
        assert response.status_code == 404

    def test_unknown_dataset_returns_410(self, client):
        resp = client.post("/api/v3/processing/run", json={"dataset_id": "missing-dataset"})
        assert resp.status_code == 410
        body = resp.json()
        assert body.get("code") == "DATASET_EXPIRED"
        assert "expired" in body.get("detail", "").lower()

    def test_missing_dataset_id_returns_422(self, client):
        resp = client.post("/api/v3/processing/run", json={})
        assert resp.status_code == 422

    def test_invalid_formula_returns_422(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/processing/run",
            json={
                "dataset_id": dataset_id,
                "user_formulas": [{"name": "Bad", "formula": "[NonExistentColumn] / 0"}],
            },
        )
        assert resp.status_code == 422

    def test_pydantic_error_response_has_detail(self, client):
        resp = client.post("/api/v3/processing/run", json={})
        body = resp.json()
        assert "detail" in body

    def test_non_json_body_returns_422(self, client):
        resp = client.post(
            "/api/v3/processing/run",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_non_finite_results_are_serialized_as_null(self, client):
        csv_content = "Time,Load,Extension\n0,10,\n1,20,0.5\n"
        upload = client.post(
            "/api/v3/datasets/upload",
            files={"file": ("nan_case.csv", csv_content, "text/csv")},
        )
        assert upload.status_code == 200, upload.text
        dataset_id = upload.json()["dataset_id"]

        resp = client.post(
            "/api/v3/processing/run",
            json={
                "dataset_id": dataset_id,
                "initial_results": {"manual_reference_index": 0},
                "derived_parameters": [{"name": "Slackness", "formula": "REF([Extension])"}],
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["results"].get("Slackness") is None


class TestFormulaPreview:
    def test_preview_success_returns_no_error_code(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[Load] * 2",
                "parameters": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body.get("error_code") is None

    def test_preview_division_error_code(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[Load] / 0",
                "parameters": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "generic"
        assert isinstance(body.get("error"), str)

    def test_preview_variable_error_code(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[DoesNotExist] + 1",
                "parameters": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "variable"
        assert isinstance(body.get("error"), str)

    def test_preview_syntax_error_code(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[Load] +",
                "parameters": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "syntax"
        assert isinstance(body.get("error"), str)

    def test_preview_unknown_dataset_returns_dataset_expired_code(self, client):
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": "missing-dataset",
                "formula": "[Load] * 2",
                "parameters": {},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "dataset_expired"
        assert "expired" in (body.get("error") or "").lower()

    def test_preview_parameter_ignores_unrelated_formula_failures(self, client):
        rows = [
            {"Width": 10.0, "Thickness": 2.0, "GaugeLength": 50.0},
            {"Width": 10.0, "Thickness": 2.0, "GaugeLength": 50.0},
        ]
        dataset_id = upload_dataset_id(client, rows)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[L0] / [A0]",
                "target_type": "parameter",
                "reference_index": 0,
                "parameters": {},
                "derived_parameters": [
                    {"name": "A0", "formula": "REF([Width]) * REF([Thickness])"},
                    {"name": "L0", "formula": "REF([GaugeLength])"},
                ],
                "user_formulas": [
                    {"name": "True Stress", "formula": "[Load] / [A0]", "enabled": True}
                ],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["is_scalar"] is True
        assert body["values"][0] == pytest.approx(2.5)


class TestFormulaPreviewReferenceIndex:
    def test_negative_reference_index_rejected(self, client):
        """reference_index must be >= 0; -1 silently maps to last row via df.iloc[-1]."""
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/formulas/preview",
            json={
                "dataset_id": dataset_id,
                "formula": "[Load] * 2",
                "parameters": {},
                "reference_index": -1,
            },
        )
        assert resp.status_code == 422


class TestReportsXlsx:
    def test_minimal_request_returns_200(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post("/api/v3/reports/xlsx", json={"dataset_id": dataset_id})
        assert resp.status_code == 200

    def test_response_content_type(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post("/api/v3/reports/xlsx", json={"dataset_id": dataset_id})
        assert "spreadsheetml" in resp.headers["content-type"]

    def test_content_disposition_header_present(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/reports/xlsx",
            json={"dataset_id": dataset_id, "project_name": "MyReport"},
        )
        disposition = resp.headers.get("content-disposition", "")
        assert "attachment" in disposition
        assert ".xlsx" in disposition

    def test_custom_filename_used(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/reports/xlsx",
            json={"dataset_id": dataset_id, "custom_filename": "my_export"},
        )
        disposition = resp.headers.get("content-disposition", "")
        assert "my_export.xlsx" in disposition

    def test_response_body_is_non_empty_bytes(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post("/api/v3/reports/xlsx", json={"dataset_id": dataset_id})
        assert len(resp.content) > 0

    def test_selected_columns_subset(self, client):
        dataset_id = upload_dataset_id(client, MINIMAL_ROWS)
        resp = client.post(
            "/api/v3/reports/xlsx",
            json={
                "dataset_id": dataset_id,
                "selected_columns": ["Time", "Load"],
            },
        )
        assert resp.status_code == 200

    def test_missing_dataset_id_returns_422(self, client):
        resp = client.post("/api/v3/reports/xlsx", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body.get("code") == "REQUEST_VALIDATION_ERROR"
        assert "errors" in body
        assert "dataset_id" in str(body["errors"])

    def test_unknown_dataset_returns_410(self, client):
        resp = client.post("/api/v3/reports/xlsx", json={"dataset_id": "missing-dataset"})
        assert resp.status_code == 410
        body = resp.json()
        assert body.get("code") == "DATASET_EXPIRED"
        assert "expired" in body.get("detail", "").lower()

    def test_pydantic_error_response_has_detail(self, client):
        resp = client.post("/api/v3/reports/xlsx", json={})
        body = resp.json()
        assert "detail" in body
        assert body.get("code") == "REQUEST_VALIDATION_ERROR"
