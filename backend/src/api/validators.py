"""Input validation utilities for API endpoints.

This module provides validation functions for file uploads and other inputs
to ensure security and data integrity.
"""

import re
from pathlib import PurePath

from fastapi import HTTPException, UploadFile

from src.utils.constants import MIN_CSV_LINES, UPLOAD_CONFIG

# Configuration
MAX_FILE_SIZE_MB = UPLOAD_CONFIG["MAX_FILE_SIZE_MB"]
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = UPLOAD_CONFIG["ALLOWED_EXTENSIONS"]
CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f]")


def validate_filename(filename: str) -> str:
    """Validate upload filename while allowing common user characters.

    Rules:
    - Non-empty and <= 255 chars
    - No path separators / traversal-like input
    - No ASCII control characters
    - Must have allowed extension
    """
    normalized = (filename or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Filename is required")
    if len(normalized) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long")
    if CONTROL_CHAR_PATTERN.search(normalized):
        raise HTTPException(status_code=400, detail="Filename contains invalid characters")
    if "/" in normalized or "\\" in normalized or PurePath(normalized).name != normalized:
        raise HTTPException(status_code=400, detail="Invalid filename path")

    suffix = PurePath(normalized).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are allowed",
        )
    return normalized


async def validate_csv_upload(
    file: UploadFile,
    max_size: int = MAX_FILE_SIZE_BYTES,
) -> bytes:
    """Validate uploaded CSV file for security and format compliance.

    Performs the following checks:
    - Filename is valid and safe
    - File extension is .csv
    - File size is within limits
    - Content is UTF-8 encoded
    - File has minimum expected structure

    Args:
        file: The uploaded file from FastAPI.
        max_size: Maximum allowed file size in bytes.

    Returns:
        File content as bytes.

    Raises:
        HTTPException: If any validation check fails.

    Example:
        @app.post("/upload")
        async def upload(file: UploadFile = File(...)):
            content = await validate_csv_upload(file)
            # Process validated content
    """
    # Validate filename and extension
    validate_filename(file.filename or "")

    # Read at most max_size + 1 bytes to detect oversized uploads without
    # loading the entire file into memory.
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Validate UTF-8 encoding
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded. Please save your CSV with UTF-8 encoding.",
        ) from exc

    # Validate minimum structure
    lines = decoded.strip().split("\n")
    if len(lines) < MIN_CSV_LINES:
        raise HTTPException(
            status_code=400,
            detail=f"CSV file has insufficient data. Expected at least {MIN_CSV_LINES} lines, got {len(lines)}.",
        )

    return content


def validate_numeric(value: float, field_name: str) -> None:
    """Validate that a numeric value is finite (allows negatives).

    Args:
        value: The value to validate.
        field_name: Name of the field for error messages.

    Raises:
        HTTPException: If value is not a finite number.
    """
    if value is None:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid number. Got: {value}",
        )
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid number. Got: {value}",
        ) from exc

    if numeric_value != numeric_value or numeric_value in (float("inf"), float("-inf")):
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a finite number. Got: {value}",
        )


def validate_parameters(params: dict, rules: dict = None) -> None:
    """Validate arbitrary parameters generically.

    Args:
        params: Dict of parameter name -> value.
        rules: Optional dict of param_name -> {max: float, required: bool}.
               Example: {"length": {"max": 10000}, "width": {"max": 1000}}

    Raises:
        HTTPException: If any parameter is invalid.

    Example:
        >>> validate_parameters(
        ...     {"length": 50.0, "width": 12.5},
        ...     rules={"length": {"max": 10000}, "width": {"max": 1000}}
        ... )
    """
    if not params:
        return

    effective_rules = rules or {}

    for name, value in params.items():
        # Skip None values
        if value is None:
            continue

        # Validate numeric (allows negatives)
        validate_numeric(value, name.replace("_", " ").title())

        # Apply max limit if defined in rules
        if name.lower() in effective_rules:
            rule = effective_rules[name.lower()]
            max_val = rule.get("max")
            if max_val and value > max_val:
                raise HTTPException(
                    status_code=400,
                    detail=f"{name} seems unreasonably large: {value}. Maximum expected: {max_val}.",
                )
