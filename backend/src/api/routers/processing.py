from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from src.api.runtime import analysis_run_store, dataset_store
from src.api.schemas import ProcessRequest, ProcessResponse, ProcessRunDataResponse
from src.api.serialization import dataframe_to_json_records, to_json_safe_value
from src.api.validators import validate_parameters
from src.core.formulas.engine import UserFormula
from src.services.processing_service import processing_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/processing", tags=["processing"])


@router.post("/run", response_model=ProcessResponse)
async def process_data(request: ProcessRequest):
    """Run data processing pipeline with operations and formulas."""
    validate_parameters(request.parameters)
    try:
        df = dataset_store.get_dataframe(request.dataset_id)
        if df is None:
            raise HTTPException(
                status_code=410,
                detail={
                    "detail": "Dataset session expired. Please re-upload your file.",
                    "code": "DATASET_EXPIRED",
                },
            )
        header_mapping = request.header_mapping or {}

        operations = [{"type": op.type, "config": op.config} for op in request.operations]
        formulas = [
            UserFormula(
                name=user_formula.name,
                formula=user_formula.formula,
                unit=user_formula.unit,
                description=user_formula.description,
            )
            for user_formula in request.user_formulas
            if user_formula.enabled
        ]
        derived_parameters_list = [
            {
                "name": derived.name,
                "formula": derived.formula,
            }
            for derived in request.derived_parameters
        ]

        processed_df, results = await asyncio.to_thread(
            processing_service.process,
            df=df,
            operations=operations,
            formulas=formulas,
            parameters=request.parameters,
            column_mapping=request.column_mapping or None,
            derived_parameters=derived_parameters_list,
            initial_results=request.initial_results or {},
            header_mapping=header_mapping,
        )
        processed_rows = dataframe_to_json_records(processed_df)
        safe_results = to_json_safe_value(results)
        snapshot = analysis_run_store.save(
            processed_data=processed_rows,
            results=safe_results,
            project_name=request.project_name,
        )

        logger.info(f"Processing complete for {request.project_name}")
        return ProcessResponse(
            processed_data=processed_rows,
            results=safe_results,
            project_name=request.project_name,
            units=request.units,
            run_id=snapshot.run_id,
        )
    except ValueError as exc:
        logger.error(f"Processing failed: {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/runs/{run_id}/data", response_model=ProcessRunDataResponse)
def get_run_data(run_id: str):
    processed_data = analysis_run_store.get_processed_data(run_id)
    if processed_data is None:
        raise HTTPException(status_code=404, detail="Run not found or expired")
    return ProcessRunDataResponse(processed_data=processed_data)
