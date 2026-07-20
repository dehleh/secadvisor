"""Pydantic schemas for billing endpoints."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.models import (
    BillingCurrency,
    BillingInterval,
    SubscriptionStatus,
    SubscriptionTier,
)


class PlanOut(BaseModel):
    """One plan from the catalog, scoped to a single currency."""
    tier: SubscriptionTier
    name: str
    description: str
    interval: BillingInterval
    currency: BillingCurrency
    amount_minor: int
    amount_major: float
    # Feature summary for the marketing card
    max_active_assessments: int | None
    max_evidence_items: int | None
    max_published_policies: int | None
    max_frameworks: int | None
    ai_advisor_enabled: bool
    custom_policy_drafting: bool
    dedicated_reviewer: bool


class PricingOut(BaseModel):
    """Plans available for the current company's currency, plus no-licence state."""
    currency: BillingCurrency
    free: PlanOut
    paid: list[PlanOut]


class CheckoutRequest(BaseModel):
    tier: SubscriptionTier
    callback_url: str | None = Field(
        default=None,
        description="URL Paystack redirects to after payment. Defaults to env config.",
    )


class CheckoutResponse(BaseModel):
    subscription_id: str
    authorization_url: str
    reference: str


class SubscriptionOut(BaseModel):
    id: str
    tier: SubscriptionTier
    interval: BillingInterval
    currency: BillingCurrency
    amount_minor: int
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    cancelled_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CurrentSubscriptionOut(BaseModel):
    """Snapshot of the company's current billing state."""
    tier: SubscriptionTier
    currency: BillingCurrency
    active_subscription: SubscriptionOut | None
