from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field, model_validator

from src.api.schemas import (
    ConfigSaveResponse,
    SavedConfigDetail,
    SavedConfigSummary,
    StatusResponse,
)
from src.core.database import delete_config, get_config_by_id, get_configs, save_config
from src.core.formulas.engine import FormulaEngine
from src.utils.constants import UPLOAD_CONFIG

router = APIRouter(prefix="/configs", tags=["configs"])

_CONFIG_DATA_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


class ConfigSaveRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field("", max_length=100)
    config_data: dict[str, Any]

    @model_validator(mode="after")
    def _check_config_size(self) -> "ConfigSaveRequest":
        if len(json.dumps(self.config_data, separators=(",", ":")).encode()) > _CONFIG_DATA_MAX_BYTES:
            raise ValueError("Configuration data exceeds maximum size of 5 MB")
        return self


@router.get("/limits")
def get_limits():
    """Return application-wide limits so the frontend doesn't need to hardcode them."""
    return {
        "max_derived_columns": FormulaEngine.MAX_FORMULAS,
        "max_file_size_mb": UPLOAD_CONFIG["MAX_FILE_SIZE_MB"],
    }


@router.post("", response_model=ConfigSaveResponse)
def create_config(request: ConfigSaveRequest):
    try:
        config_id = save_config(request.name, request.domain, request.config_data)
        return ConfigSaveResponse(status="success", id=config_id)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail=f"Configuration conflict: {exc}") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save configuration") from exc


@router.get("", response_model=list[SavedConfigSummary])
def list_configs(domain: str | None = None):
    try:
        return get_configs(domain)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to retrieve configurations") from exc


@router.get("/{config_id}", response_model=SavedConfigDetail)
def fetch_config(config_id: int = Path(..., gt=0)):
    config = get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.delete("/{config_id}", response_model=StatusResponse)
def remove_config(config_id: int = Path(..., gt=0)):
    try:
        delete_config(config_id)
        return StatusResponse(status="success")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (TypeError,) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to delete configuration") from exc
