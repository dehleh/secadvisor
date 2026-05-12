"""Reports API endpoints.

Reports are immutable artifacts produced from a submitted assessment.
They are owned by the assessment's company and inherit its tenancy.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_company, get_current_user, require_role
from app.models import Assessment, Company, Report, ReportShare, User, UserRole
from app.schemas import (
    PublicReportOut,
    ReportOut,
    ReportShareCreateRequest,
    ReportShareOut,
    ReportSummaryOut,
)


router = APIRouter(prefix="/reports", tags=["reports"])


def _scoped_report_query(db: Session, company_id: str):
    """Return a query that joins Report -> Assessment for tenant scoping."""
    return (
        db.query(Report)
        .join(Assessment, Report.assessment_id == Assessment.id)
        .filter(Assessment.company_id == company_id)
    )


def _load_company_report_or_404(db: Session, report_id: str, company_id: str) -> Report:
    report = (
        _scoped_report_query(db, company_id).filter(Report.id == report_id).first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


@router.get(
    "",
    response_model=list[ReportSummaryOut],
    summary="List reports for the current company",
)
def list_reports(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportSummaryOut]:
    rows = (
        _scoped_report_query(db, company.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [ReportSummaryOut.model_validate(r) for r in rows]


@router.get(
    "/{report_id}",
    response_model=ReportOut,
    summary="Retrieve a single report",
)
def get_report(
    report_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportOut:
    report = _load_company_report_or_404(db, report_id, company.id)
    return ReportOut.model_validate(report)


@router.get(
    "/by-assessment/{assessment_id}",
    response_model=list[ReportSummaryOut],
    summary="List all reports for a specific assessment",
)
def list_reports_for_assessment(
    assessment_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportSummaryOut]:
    # Confirm the assessment is owned by this company
    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.id == assessment_id, Assessment.company_id == company.id
        )
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    rows = (
        db.query(Report)
        .filter(Report.assessment_id == assessment_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [ReportSummaryOut.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Share links — owner / admin / member can create. Auditor is read-only and
# should NOT be able to mint share tokens.
# ---------------------------------------------------------------------------


_SHARE_WRITERS = (UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER)


@router.post(
    "/{report_id}/shares",
    response_model=ReportShareOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a public, read-only share link for a report",
)
def create_report_share(
    report_id: str,
    payload: ReportShareCreateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(require_role(*_SHARE_WRITERS))],
    db: Annotated[Session, Depends(get_db)],
) -> ReportShareOut:
    report = _load_company_report_or_404(db, report_id, company.id)

    expires_at: datetime | None = None
    if payload.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    share = ReportShare(
        report_id=report.id,
        company_id=company.id,
        created_by_user_id=user.id,
        token=secrets.token_urlsafe(32),
        label=payload.label,
        expires_at=expires_at,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return ReportShareOut.model_validate(share)


@router.get(
    "/{report_id}/shares",
    response_model=list[ReportShareOut],
    summary="List share links for a report",
)
def list_report_shares(
    report_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportShareOut]:
    _ = user  # auth-only dependency
    _load_company_report_or_404(db, report_id, company.id)
    rows = (
        db.query(ReportShare)
        .filter(ReportShare.report_id == report_id, ReportShare.company_id == company.id)
        .order_by(ReportShare.created_at.desc())
        .all()
    )
    return [ReportShareOut.model_validate(r) for r in rows]


@router.delete(
    "/shares/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a share link",
)
def revoke_report_share(
    share_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(require_role(*_SHARE_WRITERS))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    _ = user
    share = (
        db.query(ReportShare)
        .filter(ReportShare.id == share_id, ReportShare.company_id == company.id)
        .first()
    )
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found"
        )
    if share.revoked_at is None:
        share.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return None

