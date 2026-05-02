"""Billing — Paystack-backed subscription management."""
from app.services.billing.catalog import (
    CATALOG,
    PlanDefinition,
    get_plan,
    plans_for_currency,
)
from app.services.billing.limits import (
    TIER_LIMITS,
    TierLimits,
    get_limits,
    require_feature,
    require_within_limit,
)
from app.services.billing.paystack_client import (
    MockPaystackClient,
    PaystackClient,
    PaystackClientBase,
    PaystackError,
    PaystackPlan,
    PaystackSubscription,
    PaystackTransactionInit,
    get_paystack_client,
)
from app.services.billing.service import (
    cancel_subscription,
    process_webhook_event,
    record_event,
    resolve_plan_code,
    start_checkout,
)
from app.services.billing.webhook_signing import (
    compute_paystack_signature,
    verify_paystack_signature,
)

__all__ = [
    "CATALOG",
    "MockPaystackClient",
    "PaystackClient",
    "PaystackClientBase",
    "PaystackError",
    "PaystackPlan",
    "PaystackSubscription",
    "PaystackTransactionInit",
    "PlanDefinition",
    "TIER_LIMITS",
    "TierLimits",
    "cancel_subscription",
    "compute_paystack_signature",
    "get_limits",
    "get_paystack_client",
    "get_plan",
    "plans_for_currency",
    "process_webhook_event",
    "record_event",
    "require_feature",
    "require_within_limit",
    "resolve_plan_code",
    "start_checkout",
    "verify_paystack_signature",
]
