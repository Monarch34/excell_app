"""
Security tests for FormulaEngine.

These tests verify that the formula engine properly blocks
potentially dangerous operations.
"""

import pandas as pd
import pytest
from src.core.formulas import FormulaEngine


@pytest.fixture
def engine():
    """Create a FormulaEngine instance."""
    return FormulaEngine()


@pytest.fixture
def sample_df():
    """Create a simple DataFrame for testing."""
    return pd.DataFrame({"Load": [1.0, 2.0, 3.0]})


class TestSecurityImportBlocking:
    """Tests for blocking import statements."""

    def test_blocks_import_os(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("import os; [Load]", sample_df)

    def test_blocks_import_sys(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("import sys; [Load]", sample_df)

    def test_blocks_from_import(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("from os import path; [Load]", sample_df)


class TestSecurityCodeExecution:
    """Tests for blocking code execution functions."""

    def test_blocks_exec(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("exec('print(1)'); [Load]", sample_df)

    def test_blocks_eval(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("eval('1+1'); [Load]", sample_df)

    def test_blocks_compile(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("compile('1', '', 'eval'); [Load]", sample_df)


class TestSecurityDunderAccess:
    """Tests for blocking dunder attribute access."""

    def test_blocks_class_access(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("[Load].__class__", sample_df)

    def test_blocks_bases_access(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("[Load].__class__.__bases__", sample_df)

    def test_blocks_dict_access(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("[Load].__dict__", sample_df)

    def test_blocks_mro_access(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("[Load].__class__.__mro__", sample_df)


class TestSecurityFileOperations:
    """Tests for blocking file operations."""

    def test_blocks_open(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("open('/etc/passwd'); [Load]", sample_df)

    def test_blocks_file(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("file('/etc/passwd'); [Load]", sample_df)


class TestSecuritySystemAccess:
    """Tests for blocking system access."""

    def test_blocks_os_system(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("os.system('ls'); [Load]", sample_df)

    def test_blocks_subprocess(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("subprocess.call(['ls']); [Load]", sample_df)


class TestSecurityLambdaAndFunctions:
    """Tests for blocking lambda and function definitions."""

    def test_blocks_lambda(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("(lambda x: x)([Load])", sample_df)

    def test_blocks_def(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("def foo(): pass; [Load]", sample_df)


class TestSecurityAttributeAccess:
    """Tests for blocking dangerous attribute access."""

    def test_blocks_getattr(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("getattr([Load], 'shape')", sample_df)

    def test_blocks_setattr(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("setattr([Load], 'x', 1); [Load]", sample_df)

    def test_blocks_delattr(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("delattr([Load], 'x'); [Load]", sample_df)


class TestSecurityGlobalsLocals:
    """Tests for blocking globals/locals access."""

    def test_blocks_globals(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("globals(); [Load]", sample_df)

    def test_blocks_locals(self, engine, sample_df):
        with pytest.raises(ValueError):
            engine.evaluate("locals(); [Load]", sample_df)


class TestSecurityValidFormulas:
    """Tests to ensure valid formulas still work after security measures."""

    def test_valid_arithmetic_still_works(self, engine, sample_df):
        result = engine.evaluate("[Load] + 1", sample_df)
        assert len(result) == 3

    def test_valid_function_still_works(self, engine, sample_df):
        result = engine.evaluate("SQRT([Load])", sample_df)
        assert len(result) == 3

    def test_valid_complex_formula_still_works(self, engine, sample_df):
        result = engine.evaluate("ABS([Load] - 2) * 100", sample_df)
        assert len(result) == 3
