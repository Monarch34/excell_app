"""
Tests for FormulaValidator.
"""

from src.core.formulas import FormulaValidator


class TestFormulaValidatorParseReferences:
    """Tests for parse_column_references method."""

    def test_single_column_reference(self):
        validator = FormulaValidator()
        result = validator.parse_column_references("[Load]")
        assert result == ["Load"]

    def test_multiple_column_references(self):
        validator = FormulaValidator()
        result = validator.parse_column_references("[Load] + [Extension]")
        assert result == ["Load", "Extension"]

    def test_column_with_spaces(self):
        validator = FormulaValidator()
        result = validator.parse_column_references("[Tensile strain]")
        assert result == ["Tensile strain"]

    def test_complex_formula(self):
        validator = FormulaValidator()
        result = validator.parse_column_references("SQRT([True Stress]) / [Yeni Extension] * 100")
        assert result == ["True Stress", "Yeni Extension"]

    def test_no_references(self):
        validator = FormulaValidator()
        result = validator.parse_column_references("2 + 3 * 4")
        assert result == []


class TestFormulaValidatorValidate:
    """Tests for validate method."""

    def test_valid_simple_formula(self):
        validator = FormulaValidator()
        errors = validator.validate("[Load] + [Extension]", ["Load", "Extension"])
        assert errors == []

    def test_valid_formula_with_function(self):
        validator = FormulaValidator()
        errors = validator.validate("SQRT([Load])", ["Load", "Extension"])
        assert errors == []

    def test_empty_formula(self):
        validator = FormulaValidator()
        errors = validator.validate("", ["Load"])
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_whitespace_only_formula(self):
        validator = FormulaValidator()
        errors = validator.validate("   ", ["Load"])
        assert len(errors) == 1

    def test_unknown_column(self):
        validator = FormulaValidator()
        errors = validator.validate("[Unknown]", ["Load", "Extension"])
        assert len(errors) == 1
        assert "Unknown" in errors[0]

    def test_multiple_unknown_columns(self):
        validator = FormulaValidator()
        errors = validator.validate("[A] + [B]", ["Load"])
        assert len(errors) == 2
        assert any("A" in e for e in errors)
        assert any("B" in e for e in errors)

    def test_no_column_reference(self):
        validator = FormulaValidator()
        errors = validator.validate("2 + 3", ["Load"])
        assert len(errors) == 1
        assert "reference" in errors[0].lower()

    def test_unbalanced_brackets(self):
        validator = FormulaValidator()
        errors = validator.validate("[Load + Extension]", ["Load", "Extension"])
        # This should find "Load + Extension" as one column which doesn't exist
        assert len(errors) >= 1

    def test_unbalanced_parentheses(self):
        validator = FormulaValidator()
        errors = validator.validate("([Load] + [Extension]", ["Load", "Extension"])
        assert len(errors) == 1
        assert "parentheses" in errors[0].lower()


class TestFormulaValidatorSecurity:
    """Tests for security checks."""

    def test_blocks_import(self):
        validator = FormulaValidator()
        errors = validator.validate("import os", ["Load"])
        assert len(errors) >= 1
        assert any("import" in e.lower() for e in errors)

    def test_blocks_exec(self):
        validator = FormulaValidator()
        errors = validator.validate("exec('code')", ["Load"])
        assert len(errors) >= 1
        assert any("exec" in e.lower() for e in errors)

    def test_blocks_eval(self):
        validator = FormulaValidator()
        errors = validator.validate("eval('code')", ["Load"])
        assert len(errors) >= 1
        assert any("eval" in e.lower() for e in errors)

    def test_blocks_dunder(self):
        validator = FormulaValidator()
        errors = validator.validate("[Load].__class__", ["Load"])
        assert len(errors) >= 1
        assert any("__" in e for e in errors)

    def test_blocks_open(self):
        validator = FormulaValidator()
        errors = validator.validate("open('file.txt')", ["Load"])
        assert len(errors) >= 1
        assert any("open" in e.lower() for e in errors)

    def test_blocks_os(self):
        validator = FormulaValidator()
        errors = validator.validate("os.system('ls')", ["Load"])
        assert len(errors) >= 1
        assert any("os" in e.lower() for e in errors)

    def test_blocks_lambda(self):
        validator = FormulaValidator()
        errors = validator.validate("lambda x: x + 1", ["Load"])
        assert len(errors) >= 1
        assert any("lambda" in e.lower() for e in errors)


class TestFormulaValidatorNoFalsePositives:
    """
    Regression: column names containing keyword substrings must NOT be blocked.
    e.g. [evaluation_score] contains 'eval', [import_rate] contains 'import'.
    """

    def test_evaluation_score_column_not_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("[evaluation_score] * 2", ["evaluation_score"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_import_rate_column_not_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("[import_rate] / 100", ["import_rate"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_file_size_column_not_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("[file_size] + 1", ["file_size"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_globals_constant_column_not_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("[globals_constant] * 3", ["globals_constant"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_open_bracket_in_column_does_not_block(self):
        """'openness' starts with 'open' but is not the keyword 'open'."""
        validator = FormulaValidator()
        errors = validator.validate("[openness] + [Load]", ["openness", "Load"])
        assert errors == [], f"Unexpected errors: {errors}"

    # Verify actual dangerous keywords still blocked even with word-boundary matching
    def test_standalone_eval_still_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("eval('[Load]')", ["Load"])
        assert len(errors) >= 1
        assert any("eval" in e.lower() for e in errors)

    def test_standalone_import_still_blocked(self):
        validator = FormulaValidator()
        errors = validator.validate("import os", ["Load"])
        assert len(errors) >= 1
        assert any("import" in e.lower() for e in errors)


class TestFormulaValidatorColumnRefSecurity:
    """
    Regression: column names that match forbidden keywords (e.g. 'open', 'file')
    must NOT be blocked when used as bracket references.
    """

    def test_column_named_open_is_allowed(self):
        validator = FormulaValidator()
        errors = validator.validate("[open] * 2", ["open"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_columns_named_file_and_load_allowed(self):
        validator = FormulaValidator()
        errors = validator.validate("[file] + [Load]", ["file", "Load"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_bare_open_call_still_blocked(self):
        """open('x') outside a column ref must still be blocked."""
        validator = FormulaValidator()
        errors = validator.validate("open('x') + [Load]", ["Load"])
        assert len(errors) >= 1
        assert any("open" in e.lower() for e in errors)


class TestFormulaValidatorIsValid:
    """Tests for is_valid convenience method."""

    def test_valid_returns_true(self):
        validator = FormulaValidator()
        assert validator.is_valid("[Load] + [Extension]", ["Load", "Extension"]) is True

    def test_invalid_returns_false(self):
        validator = FormulaValidator()
        assert validator.is_valid("[Unknown]", ["Load"]) is False
