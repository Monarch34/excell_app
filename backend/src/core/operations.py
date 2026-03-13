"""
Generic data operations for the processing pipeline.

Each operation is a pure function: (df, config, results) -> (df, results)
Operations are domain-agnostic and configured by column names.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def find_zero(
    df: pd.DataFrame,
    config: dict[str, Any],
    results: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Find the last zero (or near-zero) in a column, then store index + value.

    Config:
        column: column name to search
        search_percent: fallback search range in the first part of data (default 0.10)
        result_key: key prefix to store results under (default: column name)
    """
    column = config.get("column")
    if column is None:
        raise ValueError("find_zero: Missing required config key 'column'")
    search_percent = config.get("search_percent", 0.10)
    result_key = config.get("result_key", column)

    if column not in df.columns:
        raise ValueError(f"find_zero: Column '{column}' not found in data")

    series = df[column]

    zero_indices = series[series == 0].index
    if not zero_indices.empty:
        index = int(zero_indices.max())
        logger.debug("find_zero: exact zero at index %s", index)
    else:
        limit = max(10, int(len(series) * search_percent))
        subset = series.iloc[:limit]
        if subset.isna().all():
            raise ValueError(f"find_zero: All values in search range of '{column}' are NaN")
        index = int(subset.abs().idxmin())
        logger.warning("find_zero: no exact zero, min abs at index %s", index)

    index_key = config.get("output_index_key", f"{result_key}_zero_index")
    value_key = config.get("output_value_key", f"{result_key}_value")
    results[index_key] = index
    results[value_key] = float(series.loc[index])

    return df, results


def slice_from_index(
    df: pd.DataFrame,
    config: dict[str, Any],
    results: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Slice DataFrame from a stored index and reset index.

    Config:
        index_key: result key holding the index to slice from
    """
    index_key = config.get("index_key")
    if index_key is None:
        raise ValueError("slice_from_index: Missing required config key 'index_key'")
    start_idx = results.get(index_key)
    if start_idx is None:
        raise ValueError(f"slice_from_index: result key '{index_key}' not found")

    df_sliced = df.loc[start_idx:].copy().reset_index(drop=True)
    logger.debug("slice_from_index: sliced from %s, %s rows remain", start_idx, len(df_sliced))
    return df_sliced, results


def offset_correction(
    df: pd.DataFrame,
    config: dict[str, Any],
    results: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Subtract row-0 values from columns, creating corrected output columns.

    Config:
        columns: list of {source: str, output: str}
        abs_value: whether to take absolute value (default False)
    """
    column_specs: list[dict[str, str]] = config.get("columns")
    if column_specs is None:
        raise ValueError("offset_correction: Missing required config key 'columns'")
    use_abs = config.get("abs_value", False)

    if df.empty:
        raise ValueError("offset_correction: DataFrame is empty, cannot compute reference row")

    for spec in column_specs:
        source = spec.get("source")
        output = spec.get("output")
        if not source or not output:
            raise ValueError("offset_correction: Each column spec must have 'source' and 'output' keys")

        if source not in df.columns:
            raise ValueError(f"offset_correction: Column '{source}' not found")

        ref_value = df[source].iloc[0]
        results[f"reference_{source}"] = float(ref_value)

        corrected = df[source] - ref_value
        if use_abs:
            corrected = corrected.abs()

        df[output] = corrected
        logger.debug("offset_correction: %s -> %s (ref=%s)", source, output, ref_value)

    return df, results


OPERATIONS = {
    "find_zero": find_zero,
    "slice_from_index": slice_from_index,
    "offset_correction": offset_correction,
}


def execute_operation(
    op_type: str,
    df: pd.DataFrame,
    config: dict[str, Any],
    results: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute a named operation."""
    func = OPERATIONS.get(op_type)
    if func is None:
        raise ValueError(
            f"Unknown operation type: '{op_type}'. Available: {list(OPERATIONS.keys())}"
        )
    return func(df, config, results)
