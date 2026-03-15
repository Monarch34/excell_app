"""
FastAPI dependency providers.

Centralises access to runtime stores and service factories so routers
receive them via ``Depends()`` instead of importing globals directly.
Tests can override any provider via ``app.dependency_overrides``.
"""

from __future__ import annotations

from src.api.analysis_run_store import AnalysisRunStore
from src.api.dataset_store import DatasetStore
from src.api.runtime import analysis_run_store, build_report_compiler, dataset_store
from src.infrastructure.config_repository import ConfigRepository
from src.services.processing_service import ProcessingService, processing_service
from src.services.report_compiler import ReportCompiler

_config_repository = ConfigRepository()


def get_dataset_store() -> DatasetStore:
    return dataset_store


def get_analysis_run_store() -> AnalysisRunStore:
    return analysis_run_store


_report_compiler: ReportCompiler | None = None


def get_report_compiler() -> ReportCompiler:
    global _report_compiler
    if _report_compiler is None:
        _report_compiler = build_report_compiler()
    return _report_compiler


def get_config_repository() -> ConfigRepository:
    return _config_repository


def get_processing_service() -> ProcessingService:
    return processing_service
