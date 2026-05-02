"""Feature gating by subscription tier.

A single source of truth for what each tier can do. Service code calls
`require_feature()` or checks `is_within_limit()` rather than hard-coding
tier comparisons all over the place — that way a pricing change is one
edit, not a grep through the codebase.

The free tier is deliberately limited but real: a founder can run an
assessment, see findings, and feel the friction of caps. Upgrade is the
escape hatch.
"""
from dataclasses import dataclass

from fastapi import HTTPException, status

from app.models import Company, SubscriptionTier


@dataclass(frozen=True)
class TierLimits:
    """What a given tier permits."""
    # Numeric caps (None = unlimited)
    max_active_assessments: int | None
    max_evidence_items: int | None
    max_published_policies: int | None
    max_frameworks: int | None  # None = all frameworks

    # Feature flags
    ai_advisor_enabled: bool
    custom_policy_drafting: bool
    dedicated_reviewer: bool
    priority_support: bool
    advanced_reporting: bool


# Single source of truth — tied to the marketing pricing table
TIER_LIMITS: dict[SubscriptionTier, TierLimits] = {
    SubscriptionTier.FREE: TierLimits(
        max_active_assessments=1,
        max_evidence_items=3,
        max_published_policies=1,
        max_frameworks=2,  # NDPA + 1 of their choice
        ai_advisor_enabled=False,  # rules-only / mock advisor for free
        custom_policy_drafting=False,
        dedicated_reviewer=False,
        priority_support=False,
        advanced_reporting=False,
    ),
    SubscriptionTier.STARTER: TierLimits(
        max_active_assessments=4,  # ~quarterly cadence
        max_evidence_items=25,
        max_published_policies=5,
        max_frameworks=2,
        ai_advisor_enabled=True,  # full AI but with caps elsewhere
        custom_policy_drafting=False,
        dedicated_reviewer=False,
        priority_support=False,
        advanced_reporting=False,
    ),
    SubscriptionTier.GROWTH: TierLimits(
        max_active_assessments=None,
        max_evidence_items=None,
        max_published_policies=None,
        max_frameworks=None,
        ai_advisor_enabled=True,
        custom_policy_drafting=False,
        dedicated_reviewer=False,
        priority_support=True,
        advanced_reporting=True,
    ),
    SubscriptionTier.AUDIT_READY: TierLimits(
        max_active_assessments=None,
        max_evidence_items=None,
        max_published_policies=None,
        max_frameworks=None,
        ai_advisor_enabled=True,
        custom_policy_drafting=True,
        dedicated_reviewer=True,
        priority_support=True,
        advanced_reporting=True,
    ),
}


def get_limits(company: Company) -> TierLimits:
    return TIER_LIMITS[company.subscription_tier]


def require_feature(company: Company, feature: str) -> None:
    """Raise 402 (Payment Required) if the company's tier lacks a feature.

    `feature` is a string attribute name on TierLimits — keeps call sites
    self-documenting: `require_feature(company, "ai_advisor_enabled")`.
    """
    limits = get_limits(company)
    if not getattr(limits, feature, False):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "tier_limit",
                "feature": feature,
                "current_tier": company.subscription_tier.value,
                "message": (
                    f"This feature requires a paid plan. "
                    f"Upgrade from {company.subscription_tier.value} to access "
                    f"{feature.replace('_', ' ')}."
                ),
            },
        )


def require_within_limit(
    company: Company,
    limit_name: str,
    current_count: int,
) -> None:
    """Raise 402 if the company is at or above their cap for a metric.

    `limit_name` is a string attribute on TierLimits like
    `max_evidence_items`. None means unlimited and never raises.
    """
    limits = get_limits(company)
    cap: int | None = getattr(limits, limit_name, None)
    if cap is None:
        return
    if current_count >= cap:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "tier_limit",
                "limit": limit_name,
                "current_tier": company.subscription_tier.value,
                "cap": cap,
                "current_count": current_count,
                "message": (
                    f"You've reached your {limit_name.replace('_', ' ')} "
                    f"limit ({cap}) for the {company.subscription_tier.value} "
                    f"plan. Upgrade to add more."
                ),
            },
        )
