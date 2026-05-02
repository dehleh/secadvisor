"""Policy API endpoints — templates, generation, acknowledgments."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import get_tenant_object_or_404
from app.database import get_db
from app.deps import get_current_company, get_current_user
from app.models import Company, Policy, PolicyAcknowledgment, User
from app.schemas import (
    PolicyAcknowledgeRequest,
    PolicyAcknowledgmentOut,
    PolicyGenerateRequest,
    PolicyOut,
    PolicySummaryOut,
    PolicyTemplateOut,
    PolicyTemplateVariableOut,
    StarterPackResponse,
)
from app.services.policies import (
    archive_policy,
    generate_policy,
    generate_starter_pack,
    get_template,
    get_templates,
    publish_policy,
)
from app.services.policies.service import acknowledge_policy as svc_acknowledge


router = APIRouter(tags=["policies"])


# ----- Templates -------------------------------------------------------------


def _serialize_template(template) -> PolicyTemplateOut:
    return PolicyTemplateOut(
        template_code=template.metadata.template_code,
        template_version=template.metadata.template_version,
        title=template.metadata.title,
        description=template.metadata.description,
        framework_codes=list(template.metadata.framework_codes),
        control_refs=[dict(c) for c in template.metadata.control_refs],
        variables=[
            PolicyTemplateVariableOut(
                name=v.name,
                label=v.display_label(),
                description=v.description,
                required=v.required,
                default=v.default,
            )
            for v in template.metadata.variables
        ],
    )


@router.get(
    "/policy-templates",
    response_model=list[PolicyTemplateOut],
    summary="List available policy templates",
)
def list_templates(
    user: Annotated[User, Depends(get_current_user)],
) -> list[PolicyTemplateOut]:
    return [_serialize_template(t) for t in sorted(
        get_templates().values(), key=lambda t: t.metadata.title
    )]


@router.get(
    "/policy-templates/{template_code}",
    response_model=PolicyTemplateOut,
    summary="Get a single template",
)
def get_template_endpoint(
    template_code: str,
    user: Annotated[User, Depends(get_current_user)],
) -> PolicyTemplateOut:
    template = get_template(template_code)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown template '{template_code}'",
        )
    return _serialize_template(template)


# ----- Policies --------------------------------------------------------------


@router.post(
    "/policies",
    response_model=PolicyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new draft policy from a template",
)
def create_policy(
    payload: PolicyGenerateRequest,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> PolicyOut:
    policy = generate_policy(
        db,
        company,
        payload.template_code,
        variable_overrides=payload.variable_overrides,
    )
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/starter-pack",
    response_model=StarterPackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate the full starter pack of policies as drafts",
)
def starter_pack(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> StarterPackResponse:
    generated = generate_starter_pack(db, company)
    return StarterPackResponse(
        generated=[PolicySummaryOut.model_validate(p) for p in generated]
    )


@router.get(
    "/policies",
    response_model=list[PolicySummaryOut],
    summary="List policies for the current company",
)
def list_policies(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PolicySummaryOut]:
    rows = (
        db.query(Policy)
        .filter(Policy.company_id == company.id)
        .order_by(Policy.created_at.desc())
        .all()
    )
    return [PolicySummaryOut.model_validate(p) for p in rows]


@router.get(
    "/policies/{policy_id}",
    response_model=PolicyOut,
    summary="Retrieve a single policy",
)
def get_policy(
    policy_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> PolicyOut:
    policy = get_tenant_object_or_404(db, Policy, policy_id, company.id)
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/{policy_id}/publish",
    response_model=PolicyOut,
    summary="Publish a draft policy (archives any prior published version)",
)
def publish(
    policy_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> PolicyOut:
    policy = get_tenant_object_or_404(db, Policy, policy_id, company.id)
    publish_policy(db, policy)
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/{policy_id}/archive",
    response_model=PolicyOut,
    summary="Archive a policy",
)
def archive(
    policy_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> PolicyOut:
    policy = get_tenant_object_or_404(db, Policy, policy_id, company.id)
    archive_policy(db, policy)
    return PolicyOut.model_validate(policy)


@router.post(
    "/policies/{policy_id}/acknowledge",
    response_model=PolicyAcknowledgmentOut,
    summary="Acknowledge a published policy",
)
def acknowledge(
    policy_id: str,
    payload: PolicyAcknowledgeRequest,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PolicyAcknowledgmentOut:
    policy = get_tenant_object_or_404(db, Policy, policy_id, company.id)
    ack = svc_acknowledge(db, policy, user, acknowledged_text=payload.acknowledged_text)
    return PolicyAcknowledgmentOut.model_validate(ack)


@router.get(
    "/policies/{policy_id}/acknowledgments",
    response_model=list[PolicyAcknowledgmentOut],
    summary="List acknowledgments for a policy",
)
def list_acknowledgments(
    policy_id: str,
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PolicyAcknowledgmentOut]:
    policy = get_tenant_object_or_404(db, Policy, policy_id, company.id)
    rows = (
        db.query(PolicyAcknowledgment)
        .filter(PolicyAcknowledgment.policy_id == policy.id)
        .order_by(PolicyAcknowledgment.created_at.desc())
        .all()
    )
    return [PolicyAcknowledgmentOut.model_validate(a) for a in rows]
