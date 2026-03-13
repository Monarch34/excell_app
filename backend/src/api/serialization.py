from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def dataframe_to_json_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Serialize a DataFrame into JSON-safe records.

    Contract:
    - Missing values are encoded as null.
    - Non-finite float values (NaN, +Inf, -Inf) are encoded as null.
    """
    replaced = df.replace([np.inf, -np.inf], np.nan)
    return replaced.astype(object).where(pd.notnull(replaced), None).to_dict(orient="records")


def to_json_safe_value(value: Any) -> Any:
    """Recursively sanitize values to be JSON compliant.

    - NaN/+Inf/-Inf -> null
    - NumPy scalar types -> native Python types
    - pandas NA/NaT -> null
    """
    if value is None:
        return None

    if isinstance(value, np.generic):
        value = value.item()

    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return value

    if isinstance(value, list | tuple):
        return [to_json_safe_value(item) for item in value]

    if isinstance(value, dict):
        return {str(key): to_json_safe_value(item) for key, item in value.items()}

    # Handles pandas NA/NaT and similar scalar null markers.
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass

    return value
