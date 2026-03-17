from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import pandas as pd

from src.api.base_store import BaseStore


@dataclass(frozen=True)
class DatasetSnapshot:
    dataset_id: str
    dataframe: pd.DataFrame
    created_at: float


class DatasetStore(BaseStore[DatasetSnapshot]):
    """In-memory store for uploaded datasets keyed by dataset_id."""

    def save(self, dataframe: pd.DataFrame) -> DatasetSnapshot:
        snapshot = DatasetSnapshot(
            dataset_id=uuid.uuid4().hex,
            dataframe=dataframe.copy(deep=True),
            created_at=time.time(),
        )
        self._put(snapshot.dataset_id, snapshot)
        return snapshot

    def get(self, dataset_id: str) -> DatasetSnapshot | None:
        return self._get(dataset_id)

    def get_dataframe(self, dataset_id: str) -> pd.DataFrame | None:
        snapshot = self.get(dataset_id)
        if snapshot is None:
            return None
        # Safe under pandas CoW mode (enabled at app startup)
        return snapshot.dataframe.copy(deep=False)
