"""
CSV Parser service for reading generic CSV files.
No domain-specific assumptions or hardcoded structures.
"""

import csv
import logging
from io import BytesIO, StringIO

import pandas as pd

logger = logging.getLogger(__name__)


class CSVParser:
    """
    Service for parsing generic CSV files.

    Example:
        >>> df, parameters, units, parameter_units = CSVParser.parse("data.csv")
    """

    @staticmethod
    def parse(
        file_path_or_buffer: str | BytesIO | StringIO,
    ) -> tuple[pd.DataFrame, dict[str, float], dict[str, str], dict[str, str]]:
        """
        Parse CSV file without assuming any domain-specific layout.
        Supports optional metadata blocks and optional units rows using
        generic heuristics.
        """
        logger.info("Parsing CSV file")

        content = CSVParser._read_content(file_path_or_buffer)
        if not content.strip():
            return pd.DataFrame(), {}, {}, {}

        lines = content.splitlines()
        if lines:
            lines[0] = lines[0].lstrip("\ufeff")

        def is_blank(line: str) -> bool:
            return not line.strip()

        # Identify metadata block (if any) and header line
        blank_idx = next((i for i, line in enumerate(lines) if is_blank(line)), None)
        metadata_lines: list[str] = []
        header_idx = None

        if blank_idx is not None:
            metadata_lines = [line for line in lines[:blank_idx] if not is_blank(line)]
            header_idx = next(
                (i for i in range(blank_idx + 1, len(lines)) if not is_blank(lines[i])), None
            )
        else:
            header_idx = next((i for i, line in enumerate(lines) if not is_blank(line)), None)

        if header_idx is None:
            return pd.DataFrame(), {}, {}, {}

        header_line = lines[header_idx].lstrip("\ufeff")
        header = CSVParser._split_csv_line(header_line)

        # Parse metadata lines into parameters (generic key/value/unit heuristic)
        parameters: dict[str, float] = {}
        parameter_units: dict[str, str] = {}
        for line in metadata_lines:
            parts = CSVParser._split_csv_line(line)
            if len(parts) < 2:
                continue
            raw_key = parts[0].strip()
            if ":" in raw_key:
                raw_key = raw_key.split(":")[-1].strip()
            value_str = parts[1].strip()
            try:
                value = float(value_str)
            except ValueError:
                continue
            if raw_key:
                parameters[raw_key] = value
                if len(parts) >= 3:
                    unit = parts[2].strip()
                    if unit:
                        parameter_units[raw_key] = unit

        # Detect optional units row
        units_dict: dict[str, str] = {}
        data_start_idx = header_idx + 1
        next_non_empty = next(
            (i for i in range(header_idx + 1, len(lines)) if not is_blank(lines[i])), None
        )
        if next_non_empty is not None:
            units_parts = CSVParser._split_csv_line(lines[next_non_empty])
            if len(units_parts) == len(header) and CSVParser._looks_like_units_row(units_parts):
                units_dict = {
                    header[i]: units_parts[i].strip()
                    for i in range(len(header))
                    if units_parts[i].strip() != ""
                }
                data_start_idx = next_non_empty + 1

        # Build CSV content for pandas from header + data rows
        data_lines = [line for line in lines[data_start_idx:] if not is_blank(line)]
        csv_text = "\n".join([header_line] + data_lines)
        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as exc:
            raise ValueError(f"Failed to parse CSV data: {exc}") from exc

        # Coerce numeric columns where possible, keep text otherwise
        for col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.notna().all():
                df[col] = numeric

        return df, parameters, units_dict, parameter_units

    @staticmethod
    def _read_content(file_path_or_buffer: str | BytesIO | StringIO) -> str:
        if hasattr(file_path_or_buffer, "read"):
            content = file_path_or_buffer.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            if hasattr(file_path_or_buffer, "seek"):
                file_path_or_buffer.seek(0)
            return content
        with open(file_path_or_buffer, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _split_csv_line(line: str) -> list[str]:
        return next(csv.reader([line]))

    @staticmethod
    def _looks_like_units_row(parts: list[str]) -> bool:
        import re as _re

        def is_number(value: str) -> bool:
            try:
                float(value)
                return True
            except ValueError:
                return False

        def is_unit_like(value: str) -> bool:
            """Short, non-numeric token containing alpha chars or unit symbols."""
            if len(value) > 20:
                return False
            if is_number(value):
                return False
            return bool(_re.search(r"[a-zA-Z°µ%/()]", value))

        trimmed = [p.strip() for p in parts]
        if not trimmed:
            return False

        numeric_count = sum(1 for p in trimmed if p and is_number(p))
        if numeric_count > 0:
            return False

        non_empty = [p for p in trimmed if p]
        if not non_empty:
            return False

        unit_count = sum(1 for p in non_empty if is_unit_like(p))
        return unit_count / len(non_empty) > 0.5

    @staticmethod
    def detect_columns(df: pd.DataFrame, patterns: dict[str, list[str]] = None) -> dict[str, str]:
        """
        Auto-detect column mappings based on naming patterns.

        Args:
            df: DataFrame with column headers
            patterns: Custom patterns dict (role -> patterns list).
                      Provided by the frontend template. If not provided,
                      returns no suggestions.

        Returns:
            Dictionary mapping role names to detected column names
        """
        suggestions = {}
        effective_patterns = patterns or {}

        for role, role_patterns in effective_patterns.items():
            for col in df.columns:
                col_lower = col.lower()
                if any(pattern in col_lower for pattern in role_patterns):
                    suggestions[role] = col
                    logger.debug(f"Auto-detected {role} -> {col}")
                    break

        logger.info(f"Auto-detected {len(suggestions)} column mappings")
        return suggestions

    @staticmethod
    def get_available_columns(df: pd.DataFrame) -> list[str]:
        """
        Get list of available column names.

        Args:
            df: DataFrame

        Returns:
            List of column names
        """
        return df.columns.tolist()

    @staticmethod
    def validate_data(df: pd.DataFrame) -> list[str]:
        """
        Validate the parsed data and return any warnings.

        Args:
            df: Parsed DataFrame

        Returns:
            List of warning messages (empty if all OK)
        """
        warnings = []

        # Check for empty DataFrame
        if df.empty:
            warnings.append("DataFrame is empty")
            return warnings

        # Check for all-null columns
        null_cols = df.columns[df.isnull().all()].tolist()
        if null_cols:
            warnings.append(f"Columns with all null values: {null_cols}")

        return warnings
