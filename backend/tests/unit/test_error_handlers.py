"""
Unit tests for src.api.error_handlers
"""

import numpy as np
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.api.error_handlers import _json_safe, register_error_handlers
from src.core.exceptions import FileFormatError, ProcessingError, ValidationError


class TestJsonSafe:
    def test_none_passthrough(self):
        assert _json_safe(None) is None

    def test_str_passthrough(self):
        assert _json_safe("hello") == "hello"

    def test_int_passthrough(self):
        assert _json_safe(1) == 1

    def test_float_passthrough(self):
        assert _json_safe(3.14) == 3.14

    def test_bool_passthrough(self):
        assert _json_safe(True) is True

    def test_numpy_int64_returns_int_not_string(self):
        result = _json_safe(np.int64(42))
        assert result == 42
        assert isinstance(result, int), f"Expected int, got {type(result)}"

    def test_numpy_float32_returns_float_not_string(self):
        result = _json_safe(np.float32(1.5))
        assert isinstance(result, float)

    def test_numpy_bool_returns_bool(self):
        result = _json_safe(np.bool_(True))
        assert result is True

    def test_list_of_numpy_scalars(self):
        result = _json_safe([np.int64(1), np.int64(2)])
        assert result == [1, 2]
        assert all(isinstance(v, int) for v in result)

    def test_dict_with_numpy_values(self):
        result = _json_safe({"x": np.int64(10)})
        assert result == {"x": 10}

    def test_unknown_type_falls_back_to_str(self):
        class Custom:
            def __str__(self):
                return "custom"

        assert _json_safe(Custom()) == "custom"

    def test_nested_structure(self):
        result = _json_safe({"a": [np.int64(1), {"b": np.float32(2.5)}]})
        assert result == {"a": [1, {"b": 2.5}]}


# ---------------------------------------------------------------------------
# Error handler integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def error_app() -> TestClient:
    """Minimal FastAPI app with error handlers registered for testing."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/validation-error")
    async def _raise_validation():
        raise ValidationError("name is required")

    @app.get("/file-format-error")
    async def _raise_file_format():
        raise FileFormatError("unsupported encoding")

    @app.get("/processing-error")
    async def _raise_processing():
        raise ProcessingError("division by zero in formula")

    @app.get("/http-error")
    async def _raise_http():
        raise HTTPException(status_code=404, detail="dataset not found")

    @app.get("/http-error-dict")
    async def _raise_http_dict():
        raise HTTPException(
            status_code=409,
            detail={"detail": "conflict", "code": "DUPLICATE"},
        )

    @app.get("/unhandled")
    async def _raise_unhandled():
        raise RuntimeError("unexpected crash")

    return TestClient(app, raise_server_exceptions=False)


class TestErrorHandlerResponses:
    def test_validation_error_returns_400(self, error_app: TestClient):
        resp = error_app.get("/validation-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"] == "name is required"
        assert body["code"] == "VALIDATION_ERROR"

    def test_file_format_error_returns_400(self, error_app: TestClient):
        resp = error_app.get("/file-format-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["detail"] == "unsupported encoding"
        assert body["code"] == "FILE_FORMAT_ERROR"

    def test_processing_error_returns_422(self, error_app: TestClient):
        resp = error_app.get("/processing-error")
        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"] == "division by zero in formula"
        assert body["code"] == "PROCESSING_ERROR"

    def test_http_exception_returns_original_status(self, error_app: TestClient):
        resp = error_app.get("/http-error")
        assert resp.status_code == 404
        body = resp.json()
        assert body["detail"] == "dataset not found"
        assert body["code"] == "HTTP_ERROR"

    def test_http_exception_with_dict_detail(self, error_app: TestClient):
        resp = error_app.get("/http-error-dict")
        assert resp.status_code == 409
        body = resp.json()
        assert body["detail"] == "conflict"
        assert body["code"] == "DUPLICATE"

    def test_unhandled_exception_returns_500(self, error_app: TestClient):
        resp = error_app.get("/unhandled")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == "INTERNAL_SERVER_ERROR"
        assert "crash" not in body["detail"].lower()
        assert "traceback" not in body["detail"].lower()
