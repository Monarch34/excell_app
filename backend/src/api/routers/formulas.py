from __future__ import annotations

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from src.api.runtime import dataset_store
from src.api.schemas import (
    DerivedParameterDef,
    FormulaPreviewRequest,
    FormulaPreviewResponse,
    UserFormulaModel,
)
from src.core.formulas.dependency import extract_references
from src.core.formulas.engine import UserFormula
from src.core.formulas.validator import FormulaValidator
from src.services.formula_context import rewrite_formula_references
from src.services.processing_service import processing_service

router = APIRouter(prefix="/formulas", tags=["formulas"])

_validator = FormulaValidator()

PREVIEW_ERROR_DIVISION = "division"
PREVIEW_ERROR_VARIABLE = "variable"
PREVIEW_ERROR_SYNTAX = "syntax"
PREVIEW_ERROR_DATASET_EXPIRED = "dataset_expired"
PREVIEW_ERROR_GENERIC = "generic"


class FormulaValidateRequest(BaseModel):
    formula: str
    available_columns: list[str] = []
    available_parameters: list[str] = []


class FormulaValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []
    referenced_columns: list[str] = []


@router.post("/validate", response_model=FormulaValidateResponse)
def validate_formula(request: FormulaValidateRequest):
    """
    Lightweight syntax + security check for a formula.
    Does NOT require any data — runs on every keystroke (debounced).
    """
    errors = _validator.validate(
        request.formula,
        available_columns=request.available_columns,
        available_parameters=request.available_parameters,
    )
    referenced = _validator.parse_column_references(request.formula)
    return FormulaValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        referenced_columns=referenced,
    )


def _iter_exception_chain(exc: Exception):
    current: Exception | None = exc
    while current is not None:
        yield current
        cause = current.__cause__
        current = cause if isinstance(cause, Exception) else None


def _classify_preview_error(exc: Exception) -> str:
    chain = list(_iter_exception_chain(exc))
    lowered_messages = " | ".join(str(item).lower() for item in chain if str(item))

    if any(isinstance(item, ZeroDivisionError) for item in chain):
        return PREVIEW_ERROR_DIVISION
    if any(isinstance(item, NameError) for item in chain):
        return PREVIEW_ERROR_VARIABLE
    if any(isinstance(item, SyntaxError) for item in chain):
        return PREVIEW_ERROR_SYNTAX

    if "division by zero" in lowered_messages or "divide by zero" in lowered_messages:
        return PREVIEW_ERROR_DIVISION
    if (
        "unknown variable" in lowered_messages
        or "not found" in lowered_messages
        or "namenotdefined" in lowered_messages
    ):
        return PREVIEW_ERROR_VARIABLE
    if "unknown or expired dataset id" in lowered_messages:
        return PREVIEW_ERROR_DATASET_EXPIRED

    if "invalid expression" in lowered_messages or "syntax" in lowered_messages:
        return PREVIEW_ERROR_SYNTAX

    return PREVIEW_ERROR_GENERIC


def _resolve_preview_dependency_closure(
    target_name: str,
    user_formulas: list[UserFormulaModel],
    derived_parameters: list[DerivedParameterDef],
) -> set[str]:
    """Return derived item names required to evaluate a specific preview target."""
    formulas_by_name: dict[str, str] = {}
    for formula in user_formulas:
        if formula.enabled and formula.name and formula.formula:
            formulas_by_name[formula.name] = formula.formula
    for param in derived_parameters:
        if param.name and param.formula:
            formulas_by_name[param.name] = param.formula

    required: set[str] = {target_name}
    stack: list[str] = [target_name]
    while stack:
        current = stack.pop()
        formula = formulas_by_name.get(current)
        if not formula:
            continue
        for ref in extract_references(formula):
            if ref in formulas_by_name and ref not in required:
                required.add(ref)
                stack.append(ref)
    return required


@router.post("/preview", response_model=FormulaPreviewResponse)
def preview_formula(request: FormulaPreviewRequest):
    """Evaluate formula on a data sample and return preview values using the main engine."""
    try:
        source_df = dataset_store.get_dataframe(request.dataset_id)
        if source_df is None:
            return FormulaPreviewResponse(
                success=False,
                error="Dataset session expired. Please re-upload your file.",
                error_code=PREVIEW_ERROR_DATASET_EXPIRED,
            )
        sample_start = max(request.sample_start, 0)
        sample_end = sample_start + request.sample_size
        df = source_df.iloc[sample_start:sample_end].copy()
        # reference_index is absolute in the dataset; preview runs on a sliced sample
        preview_reference_index = (
            request.reference_index - sample_start
            if request.reference_index is not None
            else None
        )
        header_mapping = request.header_mapping or {}

        user_formulas = list(request.user_formulas) if request.user_formulas else []
        target_name = "preview_target"

        if request.target_type == "column":
            user_formulas.append(
                UserFormulaModel(name=target_name, formula=request.formula, enabled=True)
            )
            derived_parameters = request.derived_parameters
        else:
            derived_parameters = (
                list(request.derived_parameters) if request.derived_parameters else []
            )
            derived_parameters.append(
                DerivedParameterDef(name=target_name, formula=request.formula)
            )

        # Rewrite formulas BEFORE resolving dependencies so that alias names are handled correctly!
        all_possible_columns = (
            list(df.columns)
            + [f.name for f in user_formulas if f.name != target_name]
            + [p.name for p in derived_parameters if p.name != target_name]
        )
        all_possible_params = list((request.parameters or {}).keys())

        for f in user_formulas:
            f.formula = rewrite_formula_references(
                f.formula,
                available_columns=all_possible_columns,
                available_parameters=all_possible_params,
                header_mapping=header_mapping,
                strict=False,
            )

        for p in derived_parameters:
            p.formula = rewrite_formula_references(
                p.formula,
                available_columns=all_possible_columns,
                available_parameters=all_possible_params,
                header_mapping=header_mapping,
                strict=False,
            )

        required_names = _resolve_preview_dependency_closure(
            target_name=target_name,
            user_formulas=user_formulas,
            derived_parameters=derived_parameters,
        )

        formulas = [
            UserFormula(
                name=f.name,
                formula=f.formula,
                unit=f.unit,
                description=f.description,
            )
            for f in user_formulas
            if f.enabled and f.name in required_names
        ]

        derived_parameters_list = [
            {
                "name": p.name,
                "formula": p.formula,
            }
            for p in derived_parameters
            if p.name in required_names
        ]

        initial_results = (
            {"manual_reference_index": preview_reference_index}
            if preview_reference_index is not None
            else {}
        )

        processed_df, results = processing_service.process(
            df=df,
            operations=[],
            formulas=formulas,
            parameters=request.parameters or {},
            column_mapping=request.column_mapping or {},
            derived_parameters=derived_parameters_list,
            initial_results=initial_results,
            header_mapping=header_mapping,
        )

        if request.target_type == "parameter":
            if target_name in results:
                return FormulaPreviewResponse(
                    success=True, values=[results[target_name]], is_scalar=True
                )
            elif target_name in processed_df.columns:
                values = processed_df[target_name].tolist()
                values = [value if pd.notnull(value) else None for value in values]
                if any(value is None for value in values):
                    error_code = PREVIEW_ERROR_GENERIC
                    error_msg = "Preview produced invalid numeric values"
                    return FormulaPreviewResponse(
                        success=False, error=error_msg, error_code=error_code
                    )
                return FormulaPreviewResponse(success=True, values=values, is_scalar=False)
            else:
                return FormulaPreviewResponse(
                    success=False,
                    error="Evaluation failed to produce a result",
                    error_code=PREVIEW_ERROR_GENERIC,
                )
        else:
            if target_name in processed_df.columns:
                values = processed_df[target_name].tolist()
                values = [value if pd.notnull(value) else None for value in values]
                if any(value is None for value in values):
                    error_code = PREVIEW_ERROR_GENERIC
                    error_msg = "Preview produced invalid numeric values"
                    return FormulaPreviewResponse(
                        success=False, error=error_msg, error_code=error_code
                    )
                return FormulaPreviewResponse(success=True, values=values, is_scalar=False)
            else:
                return FormulaPreviewResponse(
                    success=False,
                    error="Evaluation failed to produce a result",
                    error_code=PREVIEW_ERROR_GENERIC,
                )

    except Exception as exc:
        # Design choice: preview returns 200 + success=false so the frontend
        # can display inline error feedback without triggering global error handlers.
        error_msg = str(exc)
        error_code = _classify_preview_error(exc)
        if error_code == PREVIEW_ERROR_DIVISION:
            error_msg = "Division by zero: check that your denominator is never zero for any row"
        elif error_code == PREVIEW_ERROR_DATASET_EXPIRED:
            error_msg = "Dataset session expired. Please re-upload your file."
        return FormulaPreviewResponse(success=False, error=error_msg, error_code=error_code)
