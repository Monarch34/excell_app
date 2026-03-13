"""
Unit tests for src.api.error_handlers._json_safe
"""

import numpy as np
from src.api.error_handlers import _json_safe


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
