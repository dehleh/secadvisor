"""Roadmap service.

Roadmap items are mutable working tasks seeded from an immutable report.
The report's roadmap array is a snapshot; the RoadmapItem table is the
day-to-day surface where the company tracks progress.

Seeding is idempotent — calling seed_roadmap_from_report twice on the same
report does not duplicate items. Items already updated by the user are
preserved.
"""
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Company,
    Report,
    RoadmapItem,
    RoadmapStatus,
    User,
)


# ----- Seeding ---------------------------------------------------------------


def seed_roadmap_from_report(
    db: Session,
    company: Company,
    report: Report,
) -> list[RoadmapItem]:
    """Create RoadmapItems from a report's roadmap array.

    Idempotent: items keyed by (report_id, source_task_id). Existing items
    are not updated — call regenerate_item explicitly if you want to refresh.
    """
    if report.assessment.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report does not belong to this company",
        )

    # Existing source_task_ids for this report
    existing_ids: set[str] = {
        row.source_task_id
        for row in db.query(RoadmapItem)
        .filter(RoadmapItem.report_id == report.id)
        .all()
    }

    created: list[RoadmapItem] = []
    for task in report.roadmap or []:
        source_id = task.get("id")
        if not source_id or source_id in existing_ids:
            continue
        item = RoadmapItem(
            company_id=company.id,
            report_id=report.id,
            source_task_id=source_id,
            title=task.get("title", "Untitled task"),
            description=task.get("description", ""),
            severity=task.get("severity", "medium"),
            effort=task.get("effort", "medium"),
            week_target=task.get("week_target", 1),
            status=RoadmapStatus.TODO,
            framework_citations=task.get("framework_citations", []),
            success_criteria=task.get("success_criteria", []),
            addresses_risk_ids=task.get("addresses_risk_ids", []),
        )
        db.add(item)
        created.append(item)

    db.commit()
    for item in created:
        db.refresh(item)
    return created


# ----- Mutations -------------------------------------------------------------


def update_item(
    db: Session,
    item: RoadmapItem,
    *,
    status_value: RoadmapStatus | None = None,
    assignee: User | None = None,
    due_date: datetime | None = None,
    notes: str | None = None,
    blocked_reason: str | None = None,
) -> RoadmapItem:
    """Update mutable fields on a roadmap item.

    Status transition to DONE auto-stamps completed_at. Status transition
    away from DONE clears it.
    """
    if status_value is not None:
        if status_value == RoadmapStatus.BLOCKED and not (
            blocked_reason or item.blocked_reason
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="blocked_reason is required when transitioning to BLOCKED",
            )
        if status_value == RoadmapStatus.DONE and item.status != RoadmapStatus.DONE:
            item.completed_at = datetime.now(timezone.utc)
        elif status_value != RoadmapStatus.DONE and item.status == RoadmapStatus.DONE:
            item.completed_at = None
        item.status = status_value

    if assignee is not None:
        if assignee.company_id != item.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assignee does not belong to this company",
            )
        item.assignee_user_id = assignee.id

    if due_date is not None:
        item.due_date = due_date
    if notes is not None:
        item.notes = notes
    if blocked_reason is not None:
        item.blocked_reason = blocked_reason

    db.commit()
    db.refresh(item)
    return item


# ----- Queries ---------------------------------------------------------------


def get_roadmap_progress(
    db: Session,
    company: Company,
    *,
    report_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate progress metrics across roadmap items.

    Optionally scoped to a single report.
    """
    query = db.query(RoadmapItem).filter(RoadmapItem.company_id == company.id)
    if report_id:
        query = query.filter(RoadmapItem.report_id == report_id)
    items = query.all()

    total = len(items)
    by_status: dict[str, int] = {}
    for item in items:
        by_status[item.status.value] = by_status.get(item.status.value, 0) + 1

    done = by_status.get(RoadmapStatus.DONE.value, 0)
    in_progress = by_status.get(RoadmapStatus.IN_PROGRESS.value, 0)
    blocked = by_status.get(RoadmapStatus.BLOCKED.value, 0)

    completion_pct = round((done / total) * 100) if total else 0

    overdue = 0
    now = datetime.now(timezone.utc)
    for item in items:
        if item.status in (RoadmapStatus.DONE, RoadmapStatus.CANCELLED):
            continue
        if item.due_date and item.due_date < now:
            overdue += 1

    return {
        "total": total,
        "done": done,
        "in_progress": in_progress,
        "blocked": blocked,
        "todo": by_status.get(RoadmapStatus.TODO.value, 0),
        "cancelled": by_status.get(RoadmapStatus.CANCELLED.value, 0),
        "overdue": overdue,
        "completion_pct": completion_pct,
        "by_status": by_status,
    }
