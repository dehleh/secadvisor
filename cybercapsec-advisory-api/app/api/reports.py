"""Reports API endpoints.

Reports are immutable artifacts produced from a submitted assessment.
They are owned by the assessment's company and inherit its tenancy.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_company
from app.models import Assessment, Company, Report
from app.schemas import ReportOut, ReportSummaryOut


router = APIRouter(prefix="/reports", tags=["reports"])


def _scoped_report_query(db: Session, company_id: str):
    """Return a query that joins Report -> Assessment for tenant scoping."""
    return (
        db.query(Report)
        .join(Assessment, Report.assessment_id == Assessment.id)
        .filter(Assessment.company_id == company_id)
    )


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
    report = (
        _scoped_report_query(db, company.id)
        .filter(Report.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
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
