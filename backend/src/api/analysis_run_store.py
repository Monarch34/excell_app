from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from src.api.base_store import BaseStore


@dataclass(frozen=True)
class AnalysisRunSnapshot:
    run_id: str
    processed_data: list[dict[str, Any]]
    results: dict[str, float | int | str | bool | None]
    project_name: str
    created_at: float


class AnalysisRunStore(BaseStore[AnalysisRunSnapshot]):
    """In-memory store for recent analysis runs."""

    def save(
        self,
        *,
        processed_data: list[dict[str, Any]],
        results: dict[str, float | int | str | bool | None],
        project_name: str,
    ) -> AnalysisRunSnapshot:
        snapshot = AnalysisRunSnapshot(
            run_id=uuid.uuid4().hex,
            processed_data=[dict(row) for row in processed_data],
            results=results,
            project_name=project_name,
            created_at=time.time(),
        )
        self._put(snapshot.run_id, snapshot)
        return snapshot

    def get(self, run_id: str) -> AnalysisRunSnapshot | None:
        return self._get(run_id)

    def get_processed_data(self, run_id: str) -> list[dict[str, Any]] | None:
        snapshot = self.get(run_id)
        if snapshot is None:
            return None
        return [dict(row) for row in snapshot.processed_data]
