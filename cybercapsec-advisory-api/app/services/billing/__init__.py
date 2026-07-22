"""Billing - Flutterwave-backed subscription management."""
from app.services.billing.catalog import (
    CATALOG,
    PlanDefinition,
    get_plan,
    plans_for_currency,
)
from app.services.billing.flutterwave_client import (
    FlutterwaveClient,
    FlutterwaveClientBase,
    FlutterwaveError,
    FlutterwavePlan,
    FlutterwaveSubscription,
    FlutterwaveTransactionInit,
    MockFlutterwaveClient,
    get_flutterwave_client,
)
from app.services.billing.limits import (
    TIER_LIMITS,
    TierLimits,
    get_limits,
    require_feature,
    require_within_limit,
)
from app.services.billing.service import (
    cancel_subscription,
    process_webhook_event,
    record_event,
    resolve_plan_code,
    start_checkout,
)
from app.services.billing.webhook_signing import (
    compute_flutterwave_signature,
    verify_flutterwave_signature,
)

__all__ = [
    "CATALOG",
    "FlutterwaveClient",
    "FlutterwaveClientBase",
    "FlutterwaveError",
    "FlutterwavePlan",
    "FlutterwaveSubscription",
    "FlutterwaveTransactionInit",
    "MockFlutterwaveClient",
    "PlanDefinition",
    "TIER_LIMITS",
    "TierLimits",
    "cancel_subscription",
    "compute_flutterwave_signature",
    "get_flutterwave_client",
    "get_limits",
    "get_plan",
    "plans_for_currency",
    "process_webhook_event",
    "record_event",
    "require_feature",
    "require_within_limit",
    "resolve_plan_code",
    "start_checkout",
    "verify_flutterwave_signature",
]
