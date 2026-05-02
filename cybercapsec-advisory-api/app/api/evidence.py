"""Evidence API endpoints — create, list, control coverage queries."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import get_tenant_object_or_404
from app.database import get_db
from app.deps import get_current_company, get_current_user
from app.models import Company, Evidence, MappingStrength, User
from app.schemas import (
    ControlEvidenceOut,
    CoverageMatrixOut,
    EvidenceCreateRequest,
    EvidenceOut,
    EvidenceUpdateStatusRequest,
    EvidenceWithCoverageOut,
    PropagatedControlOut,
)
from app.services.evidence import (
    create_evidence,
    get_company_coverage_matrix,
    get_propagated_satisfaction,
    list_evidence_for_control,
    update_evidence_status,
)


router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post(
    "",
    response_model=EvidenceWithCoverageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit evidence anchored to a control",
)
def create(
    payload: EvidenceCreateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EvidenceWithCoverageOut:
    evidence = create_evidence(
        db,
        company,
        user,
        title=payload.title,
        description=payload.description,
        kind=payload.kind,
        framework_code=payload.framework_code,
        control_code=payload.control_code,
        external_url=payload.external_url,
        referenced_policy_id=payload.referenced_policy_id,
        narrative_text=payload.narrative_text,
        valid_until=payload.valid_until,
    )
    propagated = get_propagated_satisfaction(db, evidence)
    return EvidenceWithCoverageOut(
        evidence=EvidenceOut.model_validate(evidence),
        propagated_controls=[PropagatedControlOut(**p) for p in propagated],
    )


@router.get(
    "",
    response_model=list[EvidenceOut],
    summary="List all evidence for the current company",
)
def list_all(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[EvidenceOut]:
    rows = (
        db.query(Evidence)
        .filter(Evidence.company_id == company.id)
        .order_by(Evidence.created_at.desc())
        .all()
    )
    return [EvidenceOut.model_validate(r) for r in rows]


@router.get(
    "/{evidence_id}",
    response_model=EvidenceWithCoverageOut,
    summary="Retrieve evidence with its propagated coverage",
)
def get_one(
    evidence_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> EvidenceWithCoverageOut:
    evidence = get_tenant_object_or_404(db, Evidence, evidence_id, company.id)
    propagated = get_propagated_satisfaction(db, evidence)
    return EvidenceWithCoverageOut(
        evidence=EvidenceOut.model_validate(evidence),
        propagated_controls=[PropagatedControlOut(**p) for p in propagated],
    )


@router.patch(
    "/{evidence_id}/status",
    response_model=EvidenceOut,
    summary="Update evidence status",
)
def update_status(
    evidence_id: str,
    payload: EvidenceUpdateStatusRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> EvidenceOut:
    evidence = get_tenant_object_or_404(db, Evidence, evidence_id, company.id)
    update_evidence_status(db, evidence, payload.status)
    return EvidenceOut.model_validate(evidence)


@router.get(
    "/by-control/{framework_code}/{control_code}",
    response_model=ControlEvidenceOut,
    summary="List evidence for a specific control (direct + propagated)",
)
def list_by_control(
    framework_code: str,
    control_code: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> ControlEvidenceOut:
    direct, propagated = list_evidence_for_control(
        db, company, framework_code, control_code
    )
    return ControlEvidenceOut(
        framework_code=framework_code,
        control_code=control_code,
        direct_evidence=[EvidenceOut.model_validate(e) for e in direct],
        propagated_evidence=[EvidenceOut.model_validate(e) for e in propagated],
    )


@router.get(
    "/coverage/matrix",
    response_model=CoverageMatrixOut,
    summary="Per-framework coverage matrix for the current company",
)
def coverage_matrix(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> CoverageMatrixOut:
    matrix = get_company_coverage_matrix(db, company)
    # Convert sets to sorted lists for stable JSON output
    return CoverageMatrixOut(
        coverage={fw: sorted(controls) for fw, controls in matrix.items()}
    )
