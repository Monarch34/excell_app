from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.error_handlers import register_error_handlers
from src.api.middleware import (
    get_allowed_origins,
    is_explicit_cors_configured,
    request_id_middleware,
    security_headers_middleware,
)
from src.api.routers.charts import router as charts_router
from src.api.routers.configs import router as configs_router
from src.api.routers.datasets import router as datasets_router
from src.api.routers.formulas import router as formulas_router
from src.api.routers.health import router as health_router
from src.api.routers.processing import router as processing_router
from src.api.routers.reports import router as reports_router
from src.core.database import init_db


def create_app() -> FastAPI:
    import pandas as pd

    pd.set_option("mode.copy_on_write", True)

    init_db()
    app = FastAPI(title="Data Analysis API", version="3.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_allowed_origins(),
        allow_credentials=is_explicit_cors_configured(),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["Content-Disposition", "X-Request-ID"],
    )
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(request_id_middleware)
    register_error_handlers(app)

    api_v3 = APIRouter(prefix="/api/v3")
    api_v3.include_router(datasets_router)
    api_v3.include_router(formulas_router)
    api_v3.include_router(processing_router)
    api_v3.include_router(charts_router)
    api_v3.include_router(reports_router)
    api_v3.include_router(configs_router)
    api_v3.include_router(health_router)
    app.include_router(api_v3)
    return app


app = create_app()
