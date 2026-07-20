"""Guided readiness API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_company, get_current_user, require_writer
from app.models import Company, GuidedReadinessProfile, User
from app.schemas import GuidedReadinessOut, GuidedReadinessUpdateRequest


router = APIRouter(prefix="/guided-readiness", tags=["guided-readiness"])


@router.get(
    "",
    response_model=GuidedReadinessOut | None,
    summary="Fetch the current company's guided readiness state",
)
def get_profile(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> GuidedReadinessOut | None:
    profile = (
        db.query(GuidedReadinessProfile)
        .filter(GuidedReadinessProfile.company_id == company.id)
        .first()
    )
    return GuidedReadinessOut.model_validate(profile) if profile else None


@router.put(
    "",
    response_model=GuidedReadinessOut,
    summary="Create or update the current company's guided readiness state",
    dependencies=[Depends(require_writer())],
)
def upsert_profile(
    payload: GuidedReadinessUpdateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GuidedReadinessOut:
    profile = (
        db.query(GuidedReadinessProfile)
        .filter(GuidedReadinessProfile.company_id == company.id)
        .first()
    )
    if profile is None:
        profile = GuidedReadinessProfile(company_id=company.id)
        db.add(profile)

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    profile.updated_by_user_id = user.id

    db.commit()
    db.refresh(profile)
    return GuidedReadinessOut.model_validate(profile)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear the current company's guided readiness state",
    dependencies=[Depends(require_writer())],
)
def clear_profile(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    profile = (
        db.query(GuidedReadinessProfile)
        .filter(GuidedReadinessProfile.company_id == company.id)
        .first()
    )
    if profile is not None:
        db.delete(profile)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
