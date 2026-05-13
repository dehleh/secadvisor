"""Internal admin endpoints — directory of companies on the platform.

Protected by a shared ``X-Admin-Key`` header (``ADMIN_API_KEY`` env var).
This is intentionally a separate auth path from the user-facing JWT flow
so platform staff can pull marketing data without provisioning a normal
user account inside a tenant.

If ``ADMIN_API_KEY`` is unset, the endpoints respond with 503 — keeps
production safe by default until a key is explicitly provisioned.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Company, User
from app.models.assessment import Assessment, AssessmentStatus
from app.models.company import CompanySize, CompanyStage, Sector, SubscriptionTier, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])

settings = get_settings()


def require_admin_key(
    x_admin_key: Annotated[str | None, Header(alias="X-Admin-Key")] = None,
) -> None:
    """Shared-secret check for the internal admin surface."""
    if not settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is disabled (ADMIN_API_KEY not configured).",
        )
    if not x_admin_key or x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header.",
        )


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AdminCompanyOut(BaseModel):
    id: str
    name: str
    slug: str
    website: str | None
    country: str
    sector: Sector
    size: CompanySize
    stage: CompanyStage
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime

    # Aggregates / lead-gen fields
    user_count: int
    owner_email: EmailStr | None
    owner_name: str | None
    assessment_count: int
    completed_assessment_count: int
    last_assessment_at: datetime | None
    last_login_at: datetime | None  # most recent user.updated_at (proxy)

    model_config = {"from_attributes": True}


class AdminCompanyList(BaseModel):
    total: int
    items: list[AdminCompanyOut]


class AdminStatsOut(BaseModel):
    total_companies: int
    active_companies: int
    paying_companies: int
    total_users: int
    total_assessments: int
    completed_assessments: int
    by_country: dict[str, int]
    by_sector: dict[str, int]
    by_tier: dict[str, int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _company_row(db: Session, company: Company) -> AdminCompanyOut:
    """Decorate a Company row with aggregates."""
    user_count = db.query(func.count(User.id)).filter(User.company_id == company.id).scalar() or 0

    owner = (
        db.query(User)
        .filter(User.company_id == company.id, User.role == UserRole.OWNER)
        .order_by(User.created_at.asc())
        .first()
    )

    assessment_q = db.query(Assessment).filter(Assessment.company_id == company.id)
    total_assess = assessment_q.count()
    completed = assessment_q.filter(
        Assessment.status == AssessmentStatus.COMPLETED
    ).count()
    last_assess = (
        assessment_q.order_by(Assessment.created_at.desc()).first()
    )

    last_login = (
        db.query(func.max(User.updated_at))
        .filter(User.company_id == company.id)
        .scalar()
    )

    return AdminCompanyOut(
        id=company.id,
        name=company.name,
        slug=company.slug,
        website=company.website,
        country=company.country,
        sector=company.sector,
        size=company.size,
        stage=company.stage,
        subscription_tier=company.subscription_tier,
        is_active=company.is_active,
        created_at=company.created_at,
        user_count=user_count,
        owner_email=owner.email if owner else None,
        owner_name=owner.full_name if owner else None,
        assessment_count=total_assess,
        completed_assessment_count=completed,
        last_assessment_at=last_assess.created_at if last_assess else None,
        last_login_at=last_login,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/companies",
    response_model=AdminCompanyList,
    dependencies=[Depends(require_admin_key)],
    summary="List companies on the platform (marketing/CRM use)",
)
def list_companies(
    db: Annotated[Session, Depends(get_db)],
    q: str | None = Query(None, description="Substring match on name or slug"),
    country: str | None = Query(None, max_length=2, description="ISO-3166-1 alpha-2"),
    sector: Sector | None = None,
    tier: SubscriptionTier | None = None,
    is_active: bool | None = None,
    has_completed_assessment: bool | None = Query(
        None,
        description="If true, only companies with at least one completed assessment.",
    ),
    sort: Literal[
        "created_at_desc", "created_at_asc", "name_asc"
    ] = "created_at_desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return platform-wide company directory with marketing aggregates.

    Designed for outbound sales: name, country, sector, owner contact,
    activity signals (last login proxy, assessment counts).
    """
    stmt = select(Company)

    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            (func.lower(Company.name).like(like))
            | (func.lower(Company.slug).like(like))
        )
    if country:
        stmt = stmt.where(Company.country == country.upper())
    if sector:
        stmt = stmt.where(Company.sector == sector)
    if tier:
        stmt = stmt.where(Company.subscription_tier == tier)
    if is_active is not None:
        stmt = stmt.where(Company.is_active == is_active)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "created_at_asc":
        stmt = stmt.order_by(Company.created_at.asc())
    elif sort == "name_asc":
        stmt = stmt.order_by(func.lower(Company.name).asc())
    else:
        stmt = stmt.order_by(Company.created_at.desc())

    stmt = stmt.limit(limit).offset(offset)
    companies = db.scalars(stmt).all()
    items = [_company_row(db, c) for c in companies]

    if has_completed_assessment is True:
        items = [i for i in items if i.completed_assessment_count > 0]
    elif has_completed_assessment is False:
        items = [i for i in items if i.completed_assessment_count == 0]

    return AdminCompanyList(total=total, items=items)


@router.get(
    "/companies.csv",
    dependencies=[Depends(require_admin_key)],
    summary="Export companies as CSV (for upload into HubSpot/Pipedrive/etc.)",
)
def export_companies_csv(
    db: Annotated[Session, Depends(get_db)],
    country: str | None = Query(None, max_length=2),
    sector: Sector | None = None,
    tier: SubscriptionTier | None = None,
):
    stmt = select(Company)
    if country:
        stmt = stmt.where(Company.country == country.upper())
    if sector:
        stmt = stmt.where(Company.sector == sector)
    if tier:
        stmt = stmt.where(Company.subscription_tier == tier)
    stmt = stmt.order_by(Company.created_at.desc())

    companies = db.scalars(stmt).all()
    rows = [_company_row(db, c) for c in companies]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "company_name",
            "website",
            "country",
            "sector",
            "size",
            "stage",
            "subscription_tier",
            "is_active",
            "owner_name",
            "owner_email",
            "user_count",
            "assessments_total",
            "assessments_completed",
            "last_assessment_at",
            "last_login_at",
            "signed_up_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.name,
                r.website or "",
                r.country,
                r.sector.value,
                r.size.value,
                r.stage.value,
                r.subscription_tier.value,
                "yes" if r.is_active else "no",
                r.owner_name or "",
                r.owner_email or "",
                r.user_count,
                r.assessment_count,
                r.completed_assessment_count,
                r.last_assessment_at.isoformat() if r.last_assessment_at else "",
                r.last_login_at.isoformat() if r.last_login_at else "",
                r.created_at.isoformat(),
            ]
        )
    buf.seek(0)

    filename = f"ccsa-companies-{datetime.utcnow().date().isoformat()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/stats",
    response_model=AdminStatsOut,
    dependencies=[Depends(require_admin_key)],
    summary="Platform-wide aggregate metrics",
)
def get_stats(db: Annotated[Session, Depends(get_db)]):
    total_companies = db.query(func.count(Company.id)).scalar() or 0
    active_companies = (
        db.query(func.count(Company.id)).filter(Company.is_active.is_(True)).scalar()
        or 0
    )
    paying_companies = (
        db.query(func.count(Company.id))
        .filter(Company.subscription_tier != SubscriptionTier.FREE)
        .scalar()
        or 0
    )
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_assessments = db.query(func.count(Assessment.id)).scalar() or 0
    completed_assessments = (
        db.query(func.count(Assessment.id))
        .filter(Assessment.status == AssessmentStatus.COMPLETED)
        .scalar()
        or 0
    )

    by_country = dict(
        db.query(Company.country, func.count(Company.id))
        .group_by(Company.country)
        .all()
    )
    by_sector_raw = (
        db.query(Company.sector, func.count(Company.id))
        .group_by(Company.sector)
        .all()
    )
    by_sector = {s.value: n for s, n in by_sector_raw}
    by_tier_raw = (
        db.query(Company.subscription_tier, func.count(Company.id))
        .group_by(Company.subscription_tier)
        .all()
    )
    by_tier = {t.value: n for t, n in by_tier_raw}

    return AdminStatsOut(
        total_companies=total_companies,
        active_companies=active_companies,
        paying_companies=paying_companies,
        total_users=total_users,
        total_assessments=total_assessments,
        completed_assessments=completed_assessments,
        by_country=by_country,
        by_sector=by_sector,
        by_tier=by_tier,
    )
