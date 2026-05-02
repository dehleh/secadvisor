"""Policy service — orchestrates rendering and persisting policy documents.

Lifecycle:
  generate_policy()     -> creates a Policy row in DRAFT status with rendered content
  publish_policy()      -> transitions DRAFT -> PUBLISHED
  archive_policy()      -> transitions PUBLISHED -> ARCHIVED (when superseded)
  acknowledge_policy()  -> records that a user has read a published policy

Generating a new version of an already-published policy creates a new Policy
row at the next version number; the previous PUBLISHED row should be archived
once the new one is itself published.
"""
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Company,
    Policy,
    PolicyAcknowledgment,
    PolicyStatus,
    PolicyTemplateCode,
    User,
)
from app.services.policies.engine import (
    PolicyTemplate,
    TemplateRenderError,
    build_default_variables,
    get_template,
    get_templates,
    render_policy,
)


# ----- State transitions ------------------------------------------------------

ALLOWED_TRANSITIONS = {
    PolicyStatus.DRAFT: {PolicyStatus.PUBLISHED, PolicyStatus.ARCHIVED},
    PolicyStatus.PUBLISHED: {PolicyStatus.ARCHIVED},
    PolicyStatus.ARCHIVED: set(),
}


def _transition(policy: Policy, new_status: PolicyStatus) -> None:
    if new_status not in ALLOWED_TRANSITIONS[policy.status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot transition policy from {policy.status.value} "
                f"to {new_status.value}"
            ),
        )
    policy.status = new_status


# ----- Generation -------------------------------------------------------------


def _next_version(db: Session, company_id: str, template_code: str) -> int:
    """Return the next version number for a given template within a company."""
    latest = (
        db.query(Policy)
        .filter(
            Policy.company_id == company_id,
            Policy.template_code == template_code,
        )
        .order_by(Policy.version.desc())
        .first()
    )
    return (latest.version + 1) if latest else 1


def generate_policy(
    db: Session,
    company: Company,
    template_code: PolicyTemplateCode | str,
    *,
    variable_overrides: dict[str, Any] | None = None,
) -> Policy:
    """Render a template against company defaults + overrides; persist as DRAFT."""
    template = get_template(template_code)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown policy template '{template_code}'",
        )

    variables = build_default_variables(company)
    if variable_overrides:
        variables.update(variable_overrides)

    try:
        rendered = render_policy(template, variables)
    except TemplateRenderError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    policy = Policy(
        company_id=company.id,
        template_code=PolicyTemplateCode(template.metadata.template_code),
        template_version=template.metadata.template_version,
        version=_next_version(db, company.id, template.metadata.template_code),
        title=template.metadata.title,
        content=rendered,
        status=PolicyStatus.DRAFT,
        rendered_variables=variables,
        framework_codes=list(template.metadata.framework_codes),
        control_refs=list(template.metadata.control_refs),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def regenerate_policy(
    db: Session,
    company: Company,
    policy: Policy,
    *,
    variable_overrides: dict[str, Any] | None = None,
) -> Policy:
    """Create a new version of an existing policy with updated variables.

    The original policy is left untouched; the caller decides whether to
    archive it once the new version is published.
    """
    return generate_policy(
        db,
        company,
        policy.template_code,
        variable_overrides=variable_overrides,
    )


# ----- Publishing -------------------------------------------------------------


def publish_policy(db: Session, policy: Policy) -> Policy:
    """Mark a draft as published. Archives any other PUBLISHED version of the
    same template within the company so there's only one current version."""
    # Tier limit: count distinct templates currently published. Republishing
    # a different version of the same template doesn't count against quota.
    from app.models import Company
    from app.services.billing import require_within_limit

    company = db.query(Company).filter(Company.id == policy.company_id).first()
    if company is not None and policy.status != PolicyStatus.PUBLISHED:
        # Don't gate when transitioning from PUBLISHED to PUBLISHED (impossible)
        # or when the policy template is already published (sibling archive flow).
        existing_published_template = (
            db.query(Policy)
            .filter(
                Policy.company_id == company.id,
                Policy.template_code == policy.template_code,
                Policy.status == PolicyStatus.PUBLISHED,
            )
            .first()
        )
        if existing_published_template is None:
            distinct_published = (
                db.query(Policy.template_code)
                .filter(
                    Policy.company_id == company.id,
                    Policy.status == PolicyStatus.PUBLISHED,
                )
                .distinct()
                .count()
            )
            require_within_limit(
                company, "max_published_policies", distinct_published
            )

    _transition(policy, PolicyStatus.PUBLISHED)

    siblings = (
        db.query(Policy)
        .filter(
            Policy.company_id == policy.company_id,
            Policy.template_code == policy.template_code,
            Policy.status == PolicyStatus.PUBLISHED,
            Policy.id != policy.id,
        )
        .all()
    )
    for sibling in siblings:
        sibling.status = PolicyStatus.ARCHIVED

    db.commit()
    db.refresh(policy)
    return policy


def archive_policy(db: Session, policy: Policy) -> Policy:
    _transition(policy, PolicyStatus.ARCHIVED)
    db.commit()
    db.refresh(policy)
    return policy


# ----- Acknowledgment ---------------------------------------------------------


def acknowledge_policy(
    db: Session,
    policy: Policy,
    user: User,
    *,
    acknowledged_text: str | None = None,
) -> PolicyAcknowledgment:
    """Record a user's acknowledgment of a published policy.

    Idempotent — re-acknowledging returns the existing record.
    """
    if policy.status != PolicyStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only published policies can be acknowledged",
        )
    if user.company_id != policy.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this policy's company",
        )

    existing = (
        db.query(PolicyAcknowledgment)
        .filter(
            PolicyAcknowledgment.policy_id == policy.id,
            PolicyAcknowledgment.user_id == user.id,
        )
        .first()
    )
    if existing:
        return existing

    ack = PolicyAcknowledgment(
        policy_id=policy.id,
        user_id=user.id,
        acknowledged_text=acknowledged_text,
    )
    db.add(ack)
    db.commit()
    db.refresh(ack)
    return ack


# ----- Bulk generation --------------------------------------------------------


def generate_starter_pack(
    db: Session,
    company: Company,
    *,
    variable_overrides: dict[str, Any] | None = None,
) -> list[Policy]:
    """Generate one DRAFT policy per available template.

    Used at onboarding / first report submission so the company has the
    full policy starter pack ready to review and publish.
    """
    out: list[Policy] = []
    for code in get_templates():
        # Skip if a non-archived version already exists
        existing = (
            db.query(Policy)
            .filter(
                Policy.company_id == company.id,
                Policy.template_code == code,
                Policy.status != PolicyStatus.ARCHIVED,
            )
            .first()
        )
        if existing:
            continue
        policy = generate_policy(
            db, company, code, variable_overrides=variable_overrides
        )
        out.append(policy)
    return out
