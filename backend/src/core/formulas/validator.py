"""
Formula validation for security and correctness.

This module validates user-defined formulas before evaluation:
- Checks for forbidden patterns (security)
- Validates column references exist
- Checks syntax correctness
"""

import logging
import re

logger = logging.getLogger(__name__)


class FormulaValidator:
    """
    Validates user-defined formulas for security and correctness.

    Security checks:
    - Blocks dangerous patterns like import, exec, eval
    - Blocks dunder attribute access
    - Blocks file/system operations

    Correctness checks:
    - Validates column references exist in available columns
    - Checks basic syntax structure
    """

    # Patterns that are NEVER allowed in formulas
    FORBIDDEN_PATTERNS: list[str] = [
        "import",
        "exec",
        "eval",
        "__",  # Dunder access
        "open",
        "file",
        "os.",
        "sys.",
        "subprocess",
        "lambda",
        "def ",
        "class ",
        "global",
        "locals",
        "globals",
        "getattr",
        "setattr",
        "delattr",
        "compile",
        "breakpoint",
    ]

    # Regex pattern to extract column references: [Column Name]
    COLUMN_REFERENCE_PATTERN = re.compile(r"\[([^\]]+)\]")

    @staticmethod
    def _strip_column_refs(formula: str) -> str:
        """Remove ``[column_ref]`` tokens so security scans don't match column names."""
        return re.sub(r"\[[^\]]+\]", "", formula)

    def parse_column_references(self, formula: str) -> list[str]:
        """
        Extract column references from a formula.

        Column references use bracket syntax: [Column Name]

        Args:
            formula: The formula string to parse

        Returns:
            List of column names referenced in the formula

        Example:
            >>> validator = FormulaValidator()
            >>> validator.parse_column_references("[Load] / [Extension]")
            ['Load', 'Extension']
        """
        matches = self.COLUMN_REFERENCE_PATTERN.findall(formula)
        return list(matches)

    def get_referenced_columns(self, formula: str) -> list[str]:
        """Alias for parse_column_references for API consistency."""
        return self.parse_column_references(formula)

    def _find_similar_columns(
        self, target: str, available: list[str], threshold: float = 0.6
    ) -> list[str]:
        """
        Find column names similar to target using fuzzy matching.

        Args:
            target: The column name to find matches for
            available: List of available column names
            threshold: Minimum similarity ratio (0-1) to consider a match

        Returns:
            List of similar column names (up to 3)
        """
        from difflib import SequenceMatcher

        similar = []
        target_lower = target.lower()
        for col in available:
            ratio = SequenceMatcher(None, target_lower, col.lower()).ratio()
            if ratio >= threshold:
                similar.append((ratio, col))

        # Sort by similarity (highest first) and return top 3
        similar.sort(reverse=True, key=lambda x: x[0])
        return [col for _, col in similar[:3]]

    def validate(
        self, formula: str, available_columns: list[str], available_parameters: list[str] = None
    ) -> list[str]:
        """
        Validate a formula string.

        Checks:
        1. No forbidden patterns (security)
        2. All referenced columns exist
        3. At least one column is referenced
        4. Basic syntax structure

        Args:
            formula: The formula string to validate
            available_columns: List of available column names
            available_parameters: Optional list of available parameter names

        Returns:
            List of error messages. Empty list means formula is valid.

        Example:
            >>> validator = FormulaValidator()
            >>> errors = validator.validate("[Load] + [Extension]", ["Load", "Extension"])
            >>> len(errors)
            0
            >>> errors = validator.validate("[Unknown]", ["Load"])
            >>> "Unknown" in errors[0]
            True
        """
        errors: list[str] = []

        # 1. Check for empty formula
        if not formula or not formula.strip():
            errors.append("Formula cannot be empty")
            return errors

        # Strip column references before the security scan so that column names
        # like [open] or [file] do not trigger false positives.
        formula_for_security = self._strip_column_refs(formula).lower()

        # 2. Security check: forbidden patterns
        # Patterns that are plain identifiers need word-boundary matching to avoid
        # false positives on column names like [evaluation_score] or [import_rate].
        # Patterns containing punctuation (os., sys., __, def , class ) are their
        # own boundary and use a fast substring check.
        _WORD_BOUNDARY_PATTERNS = frozenset(
            {
                "import",
                "exec",
                "eval",
                "open",
                "file",
                "global",
                "locals",
                "globals",
                "getattr",
                "setattr",
                "delattr",
                "compile",
                "breakpoint",
                "lambda",
            }
        )
        for pattern in self.FORBIDDEN_PATTERNS:
            pat_lower = pattern.lower()
            if pat_lower in _WORD_BOUNDARY_PATTERNS:
                if re.search(r"\b" + re.escape(pat_lower) + r"\b", formula_for_security):
                    errors.append(f"Forbidden pattern detected: '{pattern}'")
                    logger.warning(f"Security: Blocked formula with '{pattern}'")
            else:
                if pat_lower in formula_for_security:
                    errors.append(f"Forbidden pattern detected: '{pattern}'")
                    logger.warning(f"Security: Blocked formula with '{pattern}'")

        # If security violation, return immediately
        if errors:
            return errors

        # 3. Parse column references
        referenced_columns = self.parse_column_references(formula)

        # 4. Check at least one column is referenced
        if not referenced_columns:
            errors.append("Formula must reference at least one column using [Column Name] syntax")
            return errors

        # 5. Check all referenced columns exist
        available_set: set[str] = set(available_columns)
        param_set: set[str] = set(available_parameters or [])
        all_available: set[str] = available_set | param_set

        for col in referenced_columns:
            if col not in all_available:
                # Determine what type of reference this might be
                similar_cols = self._find_similar_columns(col, available_columns)
                similar_params = self._find_similar_columns(col, available_parameters or [])

                if similar_cols:
                    errors.append(
                        f"Column not found: '{col}'. Did you mean: {', '.join(similar_cols)}?"
                    )
                elif similar_params:
                    errors.append(
                        f"Parameter not found: '{col}'. Did you mean: {', '.join(similar_params)}?"
                    )
                elif available_parameters:
                    errors.append(
                        f"Reference not found: '{col}'. "
                        f"Available columns: {', '.join(list(available_set)[:5])}{'...' if len(available_set) > 5 else ''}. "
                        f"Available parameters: {', '.join(list(param_set)[:5])}{'...' if len(param_set) > 5 else ''}."
                    )
                else:
                    errors.append(f"Column not found: '{col}'")

        # 6. Basic syntax check - balanced brackets
        open_brackets = formula.count("[")
        close_brackets = formula.count("]")
        if open_brackets != close_brackets:
            errors.append("Unbalanced brackets in formula")

        # 7. Basic syntax check - balanced parentheses
        open_parens = formula.count("(")
        close_parens = formula.count(")")
        if open_parens != close_parens:
            errors.append("Unbalanced parentheses in formula")

        return errors

    def is_valid(self, formula: str, available_columns: list[str]) -> bool:
        """
        Check if a formula is valid.

        Convenience method that returns a boolean instead of error list.

        Args:
            formula: The formula string to validate
            available_columns: List of available column names

        Returns:
            True if formula is valid, False otherwise
        """
        errors = self.validate(formula, available_columns)
        return len(errors) == 0
