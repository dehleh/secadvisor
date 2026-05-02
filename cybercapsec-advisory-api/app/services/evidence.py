"""Evidence service.

Evidence is anchored to a single (framework, control_code) pair, but via
the ControlMapping table it implicitly satisfies mapped controls in other
frameworks. This service:

  - Validates that the anchor control + framework exist in our library
    (when seeded). Until Session 6 seeds the full control library, the
    validation is best-effort: we accept any framework code that's a
    declared FrameworkCode value.
  - Persists the evidence record.
  - Computes propagated coverage on read so callers see the full picture.
"""
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Company,
    Control,
    Evidence,
    EvidenceKind,
    EvidenceStatus,
    Framework,
    FrameworkCode,
    MappingStrength,
    Policy,
    User,
)
from app.services.framework_mapping import find_related_controls


# ----- Helpers ---------------------------------------------------------------


def _validate_framework_code(framework_code: str) -> None:
    valid = {fc.value for fc in FrameworkCode}
    if framework_code not in valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown framework_code '{framework_code}'",
        )


def _validate_kind_payload(
    kind: EvidenceKind,
    external_url: str | None,
    referenced_policy_id: str | None,
    narrative_text: str | None,
) -> None:
    """Each evidence kind requires a specific payload shape."""
    if kind == EvidenceKind.EXTERNAL_LINK and not external_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="external_link evidence requires external_url",
        )
    if kind == EvidenceKind.SCREENSHOT_URL and not external_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="screenshot_url evidence requires external_url",
        )
    if kind == EvidenceKind.POLICY_REF and not referenced_policy_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="policy_ref evidence requires referenced_policy_id",
        )
    if kind == EvidenceKind.NARRATIVE and not narrative_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="narrative evidence requires narrative_text",
        )
    if kind == EvidenceKind.FILE_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="file_upload evidence is not yet supported",
        )


# ----- Lifecycle -------------------------------------------------------------


def create_evidence(
    db: Session,
    company: Company,
    user: User,
    *,
    title: str,
    description: str | None,
    kind: EvidenceKind,
    framework_code: str,
    control_code: str,
    external_url: str | None = None,
    referenced_policy_id: str | None = None,
    narrative_text: str | None = None,
    valid_until=None,
) -> Evidence:
    _validate_framework_code(framework_code)
    _validate_kind_payload(kind, external_url, referenced_policy_id, narrative_text)

    # Tier limit check — count active evidence only
    from app.models import EvidenceStatus
    from app.services.billing import require_within_limit

    current_count = (
        db.query(Evidence)
        .filter(
            Evidence.company_id == company.id,
            Evidence.status == EvidenceStatus.ACTIVE,
        )
        .count()
    )
    require_within_limit(company, "max_evidence_items", current_count)

    if referenced_policy_id:
        policy = (
            db.query(Policy)
            .filter(
                Policy.id == referenced_policy_id,
                Policy.company_id == company.id,
            )
            .first()
        )
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referenced policy not found",
            )

    evidence = Evidence(
        company_id=company.id,
        submitted_by_user_id=user.id,
        title=title,
        description=description,
        kind=kind,
        status=EvidenceStatus.ACTIVE,
        framework_code=framework_code,
        control_code=control_code,
        external_url=external_url,
        referenced_policy_id=referenced_policy_id,
        narrative_text=narrative_text,
        valid_until=valid_until,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def update_evidence_status(
    db: Session,
    evidence: Evidence,
    new_status: EvidenceStatus,
) -> Evidence:
    evidence.status = new_status
    db.commit()
    db.refresh(evidence)
    return evidence


# ----- Coverage queries -------------------------------------------------------


def get_propagated_satisfaction(
    db: Session,
    evidence: Evidence,
    *,
    min_strength: MappingStrength = MappingStrength.PARTIAL,
) -> list[dict]:
    """Return mapped controls that this evidence implicitly contributes to.

    Excludes the anchor control. Each entry: framework_code, control_code,
    title, mapping strength.
    """
    related = find_related_controls(
        db,
        framework_code=evidence.framework_code,
        control_code=evidence.control_code,
        min_strength=min_strength,
    )
    return [
        {
            "framework_code": r.framework_code,
            "control_code": r.control_code,
            "title": r.title,
            "strength": r.strength.value,
        }
        for r in related
    ]


def get_company_coverage_matrix(
    db: Session,
    company: Company,
    *,
    min_strength: MappingStrength = MappingStrength.EQUIVALENT,
) -> dict[str, set[str]]:
    """Return per-framework set of control codes the company has evidence for.

    Includes both directly-anchored controls and those implicitly satisfied
    via cross-framework mapping (defaults to EQUIVALENT-only propagation).
    """
    active_evidence = (
        db.query(Evidence)
        .filter(
            Evidence.company_id == company.id,
            Evidence.status == EvidenceStatus.ACTIVE,
        )
        .all()
    )

    pairs: list[tuple[str, str]] = [
        (e.framework_code, e.control_code) for e in active_evidence
    ]

    coverage: dict[str, set[str]] = {}
    for fw, ctrl in pairs:
        coverage.setdefault(fw, set()).add(ctrl)

    # Propagate via mapping
    for fw, ctrl in list(pairs):
        related = find_related_controls(
            db, fw, ctrl, min_strength=min_strength
        )
        for r in related:
            coverage.setdefault(r.framework_code, set()).add(r.control_code)

    return coverage


def list_evidence_for_control(
    db: Session,
    company: Company,
    framework_code: str,
    control_code: str,
    *,
    include_propagated: bool = True,
) -> tuple[list[Evidence], list[Evidence]]:
    """Return (direct_evidence, propagated_evidence) for a control.

    Direct evidence is anchored explicitly to (framework_code, control_code).
    Propagated evidence is anchored to a control that maps EQUIVALENT to this
    one — surfaced so users see what they get "for free".
    """
    direct = (
        db.query(Evidence)
        .filter(
            Evidence.company_id == company.id,
            Evidence.framework_code == framework_code,
            Evidence.control_code == control_code,
            Evidence.status == EvidenceStatus.ACTIVE,
        )
        .all()
    )

    propagated: list[Evidence] = []
    if include_propagated:
        related = find_related_controls(
            db, framework_code, control_code, min_strength=MappingStrength.EQUIVALENT
        )
        for r in related:
            rows = (
                db.query(Evidence)
                .filter(
                    Evidence.company_id == company.id,
                    Evidence.framework_code == r.framework_code,
                    Evidence.control_code == r.control_code,
                    Evidence.status == EvidenceStatus.ACTIVE,
                )
                .all()
            )
            propagated.extend(rows)

    return direct, propagated
