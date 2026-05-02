"""Subscription lifecycle service.

Three flows:

  start_checkout(company, tier)
    Creates a pending Subscription row, calls Paystack to initialize a
    transaction tied to the right plan_code, and returns the
    authorization_url that the frontend redirects the user to.

  cancel_subscription(company)
    Marks the current subscription to not auto-renew. Paystack continues
    to honour the current period; the webhook for subscription.disable
    eventually fires and we set status to CANCELLED.

  process_webhook_event(event)
    Updates Subscription state based on incoming events. This is where
    the company's tier actually changes — we never trust client-side
    "I paid!" claims, only Paystack webhooks.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    BillingEvent,
    BillingEventType,
    BillingInterval,
    Company,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
)
from app.services.billing.catalog import PlanDefinition, get_plan
from app.services.billing.paystack_client import (
    PaystackClientBase,
    PaystackError,
    PaystackTransactionInit,
)

logger = logging.getLogger(__name__)


# ----- Plan code resolution --------------------------------------------------
#
# Plan codes are populated by `app.cli sync-plans` and stored in a simple
# JSON file or env var (we use env vars for now: PAYSTACK_PLAN_<KEY>).
# The lookup key matches PlanDefinition.lookup_key.


def env_var_for_plan(plan: PlanDefinition) -> str:
    """Public helper for the env-var name used to store a plan's Paystack code."""
    safe_key = plan.lookup_key.replace(".", "_").upper()
    return f"PAYSTACK_PLAN_{safe_key}"


# Keep the underscored alias for internal call sites
_env_var_for_plan = env_var_for_plan


def resolve_plan_code(plan: PlanDefinition, env: dict[str, str]) -> str | None:
    """Look up the Paystack plan_code for a catalog plan from env vars."""
    return env.get(_env_var_for_plan(plan))


# ----- Checkout --------------------------------------------------------------


def start_checkout(
    db: Session,
    *,
    company: Company,
    user_email: str,
    tier: SubscriptionTier,
    callback_url: str,
    paystack_client: PaystackClientBase,
    plan_code_env: dict[str, str],
) -> tuple[Subscription, PaystackTransactionInit]:
    """Begin the checkout flow for a tier upgrade.

    Returns a pending Subscription row plus the Paystack init response.
    The frontend redirects to init.authorization_url. Paystack POSTs back
    to the webhook on payment success; we activate the subscription there.
    """
    if tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot checkout for the free tier",
        )

    plan = get_plan(tier=tier, currency=company.billing_currency)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No plan available for tier={tier.value} "
                f"in {company.billing_currency.value}"
            ),
        )

    plan_code = resolve_plan_code(plan, plan_code_env)
    if not plan_code:
        # In dev/mock we synthesize a plan_code via the mock client. In
        # prod, missing config should be loud — refuse rather than charge
        # without a plan binding.
        try:
            ps_plan = paystack_client.upsert_plan(
                name=plan.name,
                amount_minor=plan.amount_minor,
                currency=plan.currency.value,
                interval=plan.interval.value,
                description=plan.description,
            )
            plan_code = ps_plan.plan_code
        except PaystackError as exc:
            logger.exception("Failed to create Paystack plan on the fly")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment provider is unavailable, please try again",
            ) from exc

    # Create a pending subscription row first, then init the transaction.
    # If the transaction init fails we leave the row as PENDING and the
    # user can retry.
    sub = Subscription(
        company_id=company.id,
        tier=tier,
        interval=BillingInterval.MONTHLY,
        currency=company.billing_currency,
        amount_minor=plan.amount_minor,
        paystack_plan_code=plan_code,
        status=SubscriptionStatus.PENDING,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    try:
        init = paystack_client.initialize_transaction(
            email=user_email,
            amount_minor=plan.amount_minor,
            currency=plan.currency.value,
            plan_code=plan_code,
            callback_url=callback_url,
            metadata={
                "company_id": company.id,
                "subscription_id": sub.id,
                "tier": tier.value,
            },
        )
    except PaystackError as exc:
        logger.exception("Paystack transaction init failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider is unavailable, please try again",
        ) from exc

    return sub, init


# ----- Cancellation ----------------------------------------------------------


def cancel_subscription(
    db: Session,
    *,
    company: Company,
    paystack_client: PaystackClientBase,
) -> Subscription:
    """Cancel the active subscription. The current period is honoured."""
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.company_id == company.id,
            Subscription.status.in_(
                [SubscriptionStatus.ACTIVE, SubscriptionStatus.NON_RENEWING]
            ),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription to cancel",
        )

    if not sub.paystack_subscription_code or not sub.paystack_email_token:
        # Paystack hasn't activated this yet (still PENDING after init?)
        # We can mark it cancelled locally without calling Paystack.
        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = datetime.now(timezone.utc)
        db.commit()
        return sub

    try:
        paystack_client.disable_subscription(
            sub.paystack_subscription_code, sub.paystack_email_token
        )
    except PaystackError:
        logger.exception("Paystack disable failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider is unavailable, please try again",
        )

    # Mark for non-renewal locally. The actual transition to CANCELLED
    # happens when Paystack fires the subscription.disable webhook.
    sub.cancel_at_period_end = True
    sub.status = SubscriptionStatus.NON_RENEWING
    db.commit()
    db.refresh(sub)
    return sub


# ----- Webhook event processing ---------------------------------------------


def _classify_event(event_name: str) -> BillingEventType:
    try:
        return BillingEventType(event_name)
    except ValueError:
        return BillingEventType.OTHER


def record_event(
    db: Session,
    *,
    event_name: str,
    payload: dict[str, Any],
    paystack_event_id: str | None = None,
) -> BillingEvent | None:
    """Append-only log of webhook events. Returns None if duplicate."""
    if paystack_event_id:
        existing = (
            db.query(BillingEvent)
            .filter(BillingEvent.paystack_event_id == paystack_event_id)
            .first()
        )
        if existing:
            return None

    event_type = _classify_event(event_name)
    event = BillingEvent(
        paystack_event_id=paystack_event_id,
        event_type=event_type,
        raw_event_name=event_name,
        payload=payload,
        processed=False,
    )
    db.add(event)
    db.flush()
    return event


def process_webhook_event(
    db: Session,
    *,
    event: BillingEvent,
) -> None:
    """Apply state changes based on the event type.

    Each handler is small and idempotent — webhooks can be redelivered.
    Errors are caught at the caller and recorded in event.processing_error.
    """
    payload = event.payload
    data = payload.get("data", {}) if isinstance(payload, dict) else {}

    handler = _HANDLERS.get(event.event_type)
    if handler is None:
        logger.info(
            "Webhook event type %s has no handler; logged only",
            event.raw_event_name,
        )
    else:
        handler(db, event, data)

    event.processed = True
    db.flush()


def _find_subscription_for_event(
    db: Session, data: dict
) -> Subscription | None:
    """Try to locate the local Subscription matching a webhook payload.

    Strategy: look up by paystack_subscription_code (the canonical link),
    falling back to customer_code, falling back to metadata.subscription_id.
    """
    sub_code = data.get("subscription_code") or data.get("subscription", {}).get(
        "subscription_code"
    )
    if sub_code:
        sub = (
            db.query(Subscription)
            .filter(Subscription.paystack_subscription_code == sub_code)
            .first()
        )
        if sub:
            return sub

    metadata = data.get("metadata") or {}
    if isinstance(metadata, dict):
        sub_id = metadata.get("subscription_id")
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
            if sub:
                return sub

    customer_code = data.get("customer", {}).get("customer_code") if isinstance(
        data.get("customer"), dict
    ) else None
    if customer_code:
        # Find the most recent pending subscription for the company that
        # has this customer code.
        company = (
            db.query(Company)
            .filter(Company.paystack_customer_code == customer_code)
            .first()
        )
        if company:
            return (
                db.query(Subscription)
                .filter(
                    Subscription.company_id == company.id,
                    Subscription.status == SubscriptionStatus.PENDING,
                )
                .order_by(Subscription.created_at.desc())
                .first()
            )
    return None


def _activate_company_tier(
    db: Session, sub: Subscription
) -> None:
    """Mirror the active subscription's tier onto the company row."""
    company = db.query(Company).filter(Company.id == sub.company_id).first()
    if company is None:
        return
    company.subscription_tier = sub.tier
    company.paystack_subscription_code = sub.paystack_subscription_code
    db.flush()


def _downgrade_company_to_free(db: Session, sub: Subscription) -> None:
    company = db.query(Company).filter(Company.id == sub.company_id).first()
    if company is None:
        return
    company.subscription_tier = SubscriptionTier.FREE
    company.paystack_subscription_code = None
    db.flush()


# ----- Per-event handlers ----------------------------------------------------


def _handle_subscription_create(
    db: Session, event: BillingEvent, data: dict
) -> None:
    """Paystack confirms a subscription is now active.

    Bind paystack codes to our pending Subscription, activate it, and
    upgrade the company's tier.
    """
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        event.processing_error = (
            "subscription.create received but no matching local subscription"
        )
        return

    sub.paystack_subscription_code = data.get("subscription_code")
    sub.paystack_email_token = data.get("email_token")
    customer = data.get("customer") or {}
    if isinstance(customer, dict):
        sub.paystack_customer_code = customer.get("customer_code")

    sub.status = SubscriptionStatus.ACTIVE
    event.subscription_id = sub.id
    event.company_id = sub.company_id

    # Mirror customer code onto the company too
    company = db.query(Company).filter(Company.id == sub.company_id).first()
    if company and sub.paystack_customer_code:
        company.paystack_customer_code = sub.paystack_customer_code

    _activate_company_tier(db, sub)


def _handle_charge_success(
    db: Session, event: BillingEvent, data: dict
) -> None:
    """A successful charge — could be initial payment or renewal.

    For initial payments where the subscription hasn't yet been linked,
    this is also a chance to bind it.
    """
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return
    event.subscription_id = sub.id
    event.company_id = sub.company_id
    if sub.status in (SubscriptionStatus.PENDING, SubscriptionStatus.ATTENTION):
        sub.status = SubscriptionStatus.ACTIVE
        _activate_company_tier(db, sub)


def _handle_subscription_disable(
    db: Session, event: BillingEvent, data: dict
) -> None:
    """Paystack confirmed cancellation (end of period or admin action)."""
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return
    sub.status = SubscriptionStatus.CANCELLED
    sub.cancelled_at = datetime.now(timezone.utc)
    event.subscription_id = sub.id
    event.company_id = sub.company_id
    _downgrade_company_to_free(db, sub)


def _handle_subscription_not_renew(
    db: Session, event: BillingEvent, data: dict
) -> None:
    """Customer disabled auto-renewal. Subscription remains active until period ends."""
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return
    sub.cancel_at_period_end = True
    sub.status = SubscriptionStatus.NON_RENEWING
    event.subscription_id = sub.id
    event.company_id = sub.company_id


def _handle_invoice_payment_failed(
    db: Session, event: BillingEvent, data: dict
) -> None:
    """Renewal payment failed. Mark subscription as needing attention."""
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return
    sub.status = SubscriptionStatus.ATTENTION
    event.subscription_id = sub.id
    event.company_id = sub.company_id


_HANDLERS: dict[BillingEventType, Any] = {
    BillingEventType.SUBSCRIPTION_CREATE: _handle_subscription_create,
    BillingEventType.CHARGE_SUCCESS: _handle_charge_success,
    BillingEventType.SUBSCRIPTION_DISABLE: _handle_subscription_disable,
    BillingEventType.SUBSCRIPTION_NOT_RENEW: _handle_subscription_not_renew,
    BillingEventType.INVOICE_PAYMENT_FAILED: _handle_invoice_payment_failed,
}
