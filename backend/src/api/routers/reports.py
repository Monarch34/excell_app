from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from src.api.dataset_store import DatasetStore
from src.api.dependencies import get_dataset_store, get_report_compiler
from src.api.schemas import ExportRequest
from src.api.validators import validate_parameters
from src.services.report_compiler import ReportCompiler
from src.services.xlsx_report_builder import XlsxReportBuilder
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/xlsx")
async def export_xlsx(
    request: ExportRequest,
    ds_store: DatasetStore = Depends(get_dataset_store),
    compiler: ReportCompiler = Depends(get_report_compiler),
):
    """Generate the XLSX report."""
    logger.info(f"Report export initiated: {request.project_name}")
    validate_parameters(request.parameters)

    try:
        source_df = ds_store.get_dataframe(request.dataset_id)
        if source_df is None:
            raise HTTPException(
                status_code=410,
                detail={
                    "detail": "Dataset session expired. Please re-upload your file.",
                    "code": "DATASET_EXPIRED",
                },
            )

        compiled = await asyncio.to_thread(compiler.compile, request, source_df=source_df)
        builder = XlsxReportBuilder()
        output = await asyncio.to_thread(
            builder.build,
            df=compiled.export_df,
            column_units=compiled.column_units,
            derived_columns=compiled.derived_specs,
            metrics=compiled.metric_specs,
            parameters=compiled.parameter_specs,
            chart_images=compiled.chart_images,
            project_name=compiled.project_name,
            column_layout=compiled.column_layout,
            column_colors=compiled.column_colors,
            header_mapping=compiled.header_mapping,
        )

        filename_source = request.custom_filename or request.project_name
        safe_filename = (
            "".join(
                [char for char in filename_source if char.isalnum() or char in (" ", "-", "_")]
            ).strip()
            or "analysis_report"
        )
        logger.info(f"Report export complete: {safe_filename}")

        content_bytes = output.getvalue()
        return Response(
            content=content_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}.xlsx"',
                "Content-Length": str(len(content_bytes)),
            },
        )
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning(f"Export failed (user error): {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (KeyError, TypeError) as exc:
        logger.warning(f"Export failed (invalid input): {exc}")
        raise HTTPException(status_code=422, detail=f"Invalid export input: {exc}") from exc
    except Exception as exc:
        logger.exception("Unexpected error during export")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during export") from exc
