"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db
from app.schemas import HealthResponse


router = APIRouter(tags=["health"])

settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Return the API and database health status."""

    database_status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
        database=database_status,
    )