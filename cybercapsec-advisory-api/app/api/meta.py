"""Health and meta endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

settings = get_settings()
router = APIRouter(tags=["meta"])


@router.get("/health", summary="Liveness check")
def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@router.get("/ready", summary="Readiness check (DB connectivity)")
def ready(db: Annotated[Session, Depends(get_db)]) -> dict:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # pragma: no cover
        db_status = f"error: {exc.__class__.__name__}"
    return {"status": "ok", "database": db_status}
