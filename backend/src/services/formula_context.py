from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

import pandas as pd

from src.core.formulas.engine import FormulaEngine, UserFormula

FORMULA_REF_PATTERN = re.compile(r"\[([^\]]+)\]")

logger = logging.getLogger(__name__)


def normalize_ref_name(name: str) -> str:
    return " ".join(str(name).strip().split()).lower()


def build_formula_alias_maps(
    available_columns: list[str],
    available_parameters: list[str] | None = None,
    header_mapping: dict[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    exact: dict[str, str] = {}
    normalized: dict[str, str] = {}

    all_available = list(available_columns) + list(available_parameters or [])
    for name in all_available:
        if not isinstance(name, str):
            continue
        norm = normalize_ref_name(name)
        if norm and norm not in normalized:
            normalized[norm] = name

    if header_mapping:
        for internal_key, display_label in header_mapping.items():
            if not isinstance(internal_key, str) or not isinstance(display_label, str):
                continue
            if not display_label.strip():
                continue
            exact[display_label] = internal_key
            norm_label = normalize_ref_name(display_label)
            if norm_label:
                normalized[norm_label] = internal_key

    return exact, normalized


def resolve_fuzzy_reference(
    token: str,
    available_columns: list[str],
    available_parameters: list[str] | None = None,
) -> str | None:
    candidates = [col for col in available_columns if isinstance(col, str)] + [
        param for param in (available_parameters or []) if isinstance(param, str)
    ]
    if not candidates:
        return None

    token_norm = normalize_ref_name(token)
    if not token_norm:
        return None

    token_words = {word for word in re.split(r"\W+", token_norm) if len(word) > 2}
    scored: list[tuple[float, str]] = []
    for candidate in candidates:
        cand_norm = normalize_ref_name(candidate)
        if not cand_norm:
            continue
        score = SequenceMatcher(None, token_norm, cand_norm).ratio()
        if token_words:
            cand_words = {word for word in re.split(r"\W+", cand_norm) if len(word) > 2}
            if token_words & cand_words:
                score += 0.08
        scored.append((score, candidate))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_name = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0
    if best_score >= 0.70 and (best_score - second_score) >= 0.05:
        return best_name
    return None


def rewrite_formula_references(
    formula: str,
    available_columns: list[str],
    available_parameters: list[str] | None = None,
    header_mapping: dict[str, str] | None = None,
    strict: bool = True,
) -> str:
    if not formula:
        return formula

    exact_aliases, normalized_aliases = build_formula_alias_maps(
        available_columns=available_columns,
        available_parameters=available_parameters,
        header_mapping=header_mapping,
    )

    def replace_ref(match: re.Match[str]) -> str:
        token = match.group(1)
        if token in exact_aliases:
            return f"[{exact_aliases[token]}]"
        norm = normalize_ref_name(token)
        resolved = normalized_aliases.get(norm)
        if resolved:
            return f"[{resolved}]"
        if strict:
            return match.group(0)
        fuzzy = resolve_fuzzy_reference(token, available_columns, available_parameters)
        if fuzzy:
            logger.warning("Fuzzy-matched formula reference [%s] -> [%s]", token, fuzzy)
        return f"[{fuzzy}]" if fuzzy else match.group(0)

    return FORMULA_REF_PATTERN.sub(replace_ref, formula)


def apply_cut_point(
    df: pd.DataFrame,
    formulas: list[UserFormula],
    params: dict[str, float],
    reference_index: int | None,
    formula_engine: FormulaEngine | None = None,
) -> pd.DataFrame:
    engine = formula_engine or FormulaEngine()
    if reference_index is None or reference_index < 0:
        return engine.apply_formulas(
            df, formulas, parameters=params, reference_index=reference_index
        )

    if reference_index >= len(df):
        logger.warning(
            "reference_index %d is out of bounds (dataframe has %d rows); "
            "all derived columns will be NaN",
            reference_index,
            len(df),
        )
        result_df = df.copy()
        for formula in formulas:
            result_df[formula.name] = float("nan")
        return result_df

    before_ref = df.iloc[:reference_index].copy()
    from_ref = df.iloc[reference_index:].copy()
    from_ref = engine.apply_formulas(from_ref, formulas, parameters=params, reference_index=0)
    for formula in formulas:
        before_ref[formula.name] = float("nan")
    return pd.concat([before_ref, from_ref], ignore_index=False)
