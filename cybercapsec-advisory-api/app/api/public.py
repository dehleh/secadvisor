"""Public, unauthenticated endpoints for tokenised share links."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assessment, Company, Report, ReportShare
from app.schemas import PublicReportOut


router = APIRouter(prefix="/public", tags=["public"])


@router.get(
    "/reports/{token}",
    response_model=PublicReportOut,
    summary="Fetch a report via a public share token (no auth)",
)
def get_public_report(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> PublicReportOut:
    share = db.query(ReportShare).filter(ReportShare.token == token).first()
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found"
        )

    now = datetime.now(timezone.utc)
    if share.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Share link has been revoked"
        )
    # SQLAlchemy may return naive datetimes depending on driver; normalise.
    expires = share.expires_at
    if expires is not None and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires is not None and expires < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Share link has expired"
        )

    report = db.query(Report).filter(Report.id == share.report_id).first()
    assessment = (
        db.query(Assessment).filter(Assessment.id == report.assessment_id).first()
        if report
        else None
    )
    company = (
        db.query(Company).filter(Company.id == share.company_id).first()
    )
    if not (report and assessment and company):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not available"
        )

    # Light analytics
    share.view_count = (share.view_count or 0) + 1
    share.last_viewed_at = now
    db.commit()

    return PublicReportOut(
        company_name=company.name,
        report_type=report.report_type,
        executive_summary=report.executive_summary,
        risk_register=list(report.risk_register or []),
        roadmap=list(report.roadmap or []),
        framework_gaps=dict(report.framework_gaps or {}),
        overall_risk_score=assessment.overall_risk_score,
        soc2_readiness_score=assessment.soc2_readiness_score,
        ndpa_compliance_score=assessment.ndpa_compliance_score,
        generated_at=report.created_at,
        label=share.label,
    )
