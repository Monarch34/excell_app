from __future__ import annotations

import asyncio
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.api.dataset_store import DatasetStore
from src.api.dependencies import get_dataset_store
from src.api.schemas import DetectColumnsResponse, UploadResponse
from src.api.serialization import dataframe_to_json_records, to_json_safe_value
from src.api.validators import validate_csv_upload
from src.services.csv_parser import CSVParser
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])
UPLOAD_FILE_REQUIRED = File(...)


class DetectColumnsRequest(BaseModel):
    data: list[dict] = Field(default_factory=list)
    patterns: dict[str, list[str]] | None = None


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = UPLOAD_FILE_REQUIRED,
    ds_store: DatasetStore = Depends(get_dataset_store),
):
    """Upload CSV file and return dataset_id + dataset preview metadata."""
    logger.info(f"File upload initiated: {file.filename}")
    content = await validate_csv_upload(file)
    try:
        df, parameters, units, parameter_units = CSVParser.parse(BytesIO(content))
    except Exception as exc:
        logger.warning(f"CSV parse failed for {file.filename}: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    snapshot = ds_store.save(df)
    serializable_df = df.where(pd.notnull(df), None)
    dtypes: dict[str, str] = {}
    for column in df.columns:
        dtypes[column] = "numeric" if pd.api.types.is_numeric_dtype(df[column]) else "text"

    logger.info(
        f"Successfully processed {file.filename}: {len(serializable_df)} rows, {len(serializable_df.columns)} columns"
    )
    response_payload = {
        "dataset_id": snapshot.dataset_id,
        "filename": file.filename,
        "raw_data": dataframe_to_json_records(serializable_df),
        "parameters": parameters,
        "parameter_units": parameter_units,
        "units": units,
        "columns": list(serializable_df.columns),
        "dtypes": dtypes,
    }
    return to_json_safe_value(response_payload)


@router.post("/detect-columns", response_model=DetectColumnsResponse)
async def detect_columns(request: DetectColumnsRequest):
    df = pd.DataFrame(request.data)
    suggestions = await asyncio.to_thread(CSVParser.detect_columns, df, request.patterns)
    return DetectColumnsResponse(suggestions=suggestions)
