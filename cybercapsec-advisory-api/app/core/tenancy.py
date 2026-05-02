"""Multi-tenancy enforcement.

All queries that touch tenant-scoped data must run through these helpers,
which guarantee a row belongs to the caller's company.
"""
from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


def get_tenant_object_or_404(
    db: Session,
    model: Type[T],
    object_id: str,
    company_id: str,
    company_id_field: str = "company_id",
) -> T:
    """Fetch an object scoped to a company, raising 404 if not found.

    This is the single chokepoint for tenant-scoped reads. If a model uses
    a different field for tenant scoping, pass `company_id_field`.
    """
    column = getattr(model, company_id_field, None)
    if column is None:
        raise ValueError(
            f"Model {model.__name__} has no field '{company_id_field}' for tenancy scoping"
        )

    obj = (
        db.query(model)
        .filter(model.id == object_id, column == company_id)
        .first()
    )
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found",
        )
    return obj
