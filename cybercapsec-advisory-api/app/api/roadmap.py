"""Roadmap API endpoints — seed from report, track tasks, query progress."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import get_tenant_object_or_404
from app.database import get_db
from app.deps import get_current_company, require_writer
from app.models import Assessment, Company, Report, RoadmapItem, User
from app.schemas import (
    RoadmapItemOut,
    RoadmapItemUpdateRequest,
    RoadmapProgressOut,
    RoadmapSeedResponse,
)
from app.services.roadmap import (
    get_roadmap_progress,
    seed_roadmap_from_report,
    update_item,
)


router = APIRouter(prefix="/roadmap", tags=["roadmap"])


def _get_report_scoped(db: Session, report_id: str, company_id: str) -> Report:
    report = (
        db.query(Report)
        .join(Assessment, Report.assessment_id == Assessment.id)
        .filter(Report.id == report_id, Assessment.company_id == company_id)
        .first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


@router.post(
    "/seed-from-report/{report_id}",
    response_model=RoadmapSeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Seed roadmap items from a report's roadmap array (idempotent)",
    dependencies=[Depends(require_writer())],
)
def seed(
    report_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> RoadmapSeedResponse:
    report = _get_report_scoped(db, report_id, company.id)
    items = seed_roadmap_from_report(db, company, report)
    return RoadmapSeedResponse(
        seeded=len(items),
        items=[RoadmapItemOut.model_validate(i) for i in items],
    )


@router.get(
    "/items",
    response_model=list[RoadmapItemOut],
    summary="List roadmap items for the current company",
)
def list_items(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
    report_id: str | None = None,
    status_filter: str | None = None,
) -> list[RoadmapItemOut]:
    query = db.query(RoadmapItem).filter(RoadmapItem.company_id == company.id)
    if report_id:
        query = query.filter(RoadmapItem.report_id == report_id)
    if status_filter:
        query = query.filter(RoadmapItem.status == status_filter)
    rows = query.order_by(
        RoadmapItem.week_target.asc(), RoadmapItem.created_at.asc()
    ).all()
    return [RoadmapItemOut.model_validate(r) for r in rows]


@router.get(
    "/items/{item_id}",
    response_model=RoadmapItemOut,
    summary="Retrieve a roadmap item",
)
def get_item(
    item_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> RoadmapItemOut:
    item = get_tenant_object_or_404(db, RoadmapItem, item_id, company.id)
    return RoadmapItemOut.model_validate(item)


@router.patch(
    "/items/{item_id}",
    response_model=RoadmapItemOut,
    summary="Update a roadmap item (status, assignee, due date, notes)",
    dependencies=[Depends(require_writer())],
)
def update_item_endpoint(
    item_id: str,
    payload: RoadmapItemUpdateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> RoadmapItemOut:
    item = get_tenant_object_or_404(db, RoadmapItem, item_id, company.id)

    assignee: User | None = None
    if payload.assignee_user_id:
        assignee = (
            db.query(User)
            .filter(
                User.id == payload.assignee_user_id, User.company_id == company.id
            )
            .first()
        )
        if assignee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignee user not found in this company",
            )

    update_item(
        db,
        item,
        status_value=payload.status,
        assignee=assignee,
        due_date=payload.due_date,
        notes=payload.notes,
        blocked_reason=payload.blocked_reason,
    )
    return RoadmapItemOut.model_validate(item)


@router.get(
    "/progress",
    response_model=RoadmapProgressOut,
    summary="Aggregate roadmap progress",
)
def progress(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
    report_id: str | None = None,
) -> RoadmapProgressOut:
    return RoadmapProgressOut(
        **get_roadmap_progress(db, company, report_id=report_id)
    )
