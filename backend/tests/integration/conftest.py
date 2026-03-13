"""
Integration test specific fixtures.
"""

import pytest


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test output files."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir
