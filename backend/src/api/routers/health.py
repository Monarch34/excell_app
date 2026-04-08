from __future__ import annotations

import sqlite3

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.core.database import DB_PATH

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health_check():
    db_ok = False
    try:
        conn = sqlite3.connect(DB_PATH, timeout=2)
        conn.execute("SELECT 1")
        conn.close()
        db_ok = True
    except Exception:
        pass

    status = "ok" if db_ok else "degraded"
    return HealthResponse(status=status, version="3.0.0", db_connected=db_ok)
