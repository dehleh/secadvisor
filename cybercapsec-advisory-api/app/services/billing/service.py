"""Subscription lifecycle service.

Checkout and webhook processing are Flutterwave-backed. The database still has
legacy paystack_* column names; those columns store Flutterwave identifiers until
a separate migration can safely rename them.
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
from app.services.billing.flutterwave_client import (
    FlutterwaveClientBase,
    FlutterwaveError,
    FlutterwaveTransactionInit,
)

logger = logging.getLogger(__name__)


def env_var_for_plan(plan: PlanDefinition) -> str:
    """Env-var name used to store a Flutterwave payment plan ID."""
    safe_key = plan.lookup_key.replace(".", "_").upper()
    return f"FLUTTERWAVE_PLAN_{safe_key}"


_env_var_for_plan = env_var_for_plan


def resolve_plan_code(plan: PlanDefinition, env: dict[str, str]) -> str | None:
    """Look up the Flutterwave payment plan ID for a catalog plan."""
    return env.get(_env_var_for_plan(plan))


def start_checkout(
    db: Session,
    *,
    company: Company,
    user_email: str,
    tier: SubscriptionTier,
    callback_url: str,
    flutterwave_client: FlutterwaveClientBase,
    plan_code_env: dict[str, str],
) -> tuple[Subscription, FlutterwaveTransactionInit]:
    """Begin checkout for a tier upgrade."""
    if tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot checkout for the no-licence state",
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
        try:
            provider_plan = flutterwave_client.upsert_plan(
                name=plan.provider_name,
                amount_minor=plan.amount_minor,
                currency=plan.currency.value,
                interval=plan.interval.value,
                description=plan.description,
            )
            plan_code = provider_plan.plan_code
        except FlutterwaveError as exc:
            logger.exception("Failed to create Flutterwave plan on the fly")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment provider is unavailable, please try again",
            ) from exc

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
        init = flutterwave_client.initialize_transaction(
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
    except FlutterwaveError as exc:
        logger.exception("Flutterwave checkout init failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider is unavailable, please try again",
        ) from exc

    return sub, init


def cancel_subscription(
    db: Session,
    *,
    company: Company,
    flutterwave_client: FlutterwaveClientBase,
) -> Subscription:
    """Cancel the active subscription."""
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

    if sub.paystack_subscription_code:
        try:
            flutterwave_client.disable_subscription(
                sub.paystack_subscription_code,
                sub.paystack_email_token,
            )
        except FlutterwaveError:
            logger.exception("Flutterwave cancellation failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment provider is unavailable, please try again",
            )

    sub.status = SubscriptionStatus.CANCELLED
    sub.cancelled_at = datetime.now(timezone.utc)
    sub.cancel_at_period_end = False
    _downgrade_company_to_free(db, sub)
    db.commit()
    db.refresh(sub)
    return sub


def _classify_event(event_name: str) -> BillingEventType:
    mapped = {
        "charge.completed": BillingEventType.CHARGE_SUCCESS,
        "charge.successful": BillingEventType.CHARGE_SUCCESS,
        "charge.success": BillingEventType.CHARGE_SUCCESS,
        "charge.failed": BillingEventType.CHARGE_FAILED,
        "subscription.created": BillingEventType.SUBSCRIPTION_CREATE,
        "subscription.create": BillingEventType.SUBSCRIPTION_CREATE,
        "subscription.cancelled": BillingEventType.SUBSCRIPTION_DISABLE,
        "subscription.cancelled_or_deactivated": BillingEventType.SUBSCRIPTION_DISABLE,
        "subscription.disable": BillingEventType.SUBSCRIPTION_DISABLE,
        "subscription.payment_failed": BillingEventType.INVOICE_PAYMENT_FAILED,
        "invoice.payment_failed": BillingEventType.INVOICE_PAYMENT_FAILED,
    }
    if event_name in mapped:
        return mapped[event_name]
    try:
        return BillingEventType(event_name)
    except ValueError:
        return BillingEventType.OTHER


def record_event(
    db: Session,
    *,
    event_name: str,
    payload: dict[str, Any],
    provider_event_id: str | None = None,
) -> BillingEvent | None:
    """Append-only log of webhook events. Returns None if duplicate."""
    if provider_event_id:
        existing = (
            db.query(BillingEvent)
            .filter(BillingEvent.paystack_event_id == provider_event_id)
            .first()
        )
        if existing:
            return None

    event = BillingEvent(
        paystack_event_id=provider_event_id,
        event_type=_classify_event(event_name),
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
    """Apply idempotent state changes for a stored webhook event."""
    payload = event.payload
    data = payload.get("data", {}) if isinstance(payload, dict) else {}

    handler = _HANDLERS.get(event.event_type)
    if handler is None:
        logger.info("Webhook event type %s has no handler", event.raw_event_name)
    else:
        handler(db, event, data)

    event.processed = True
    db.flush()


def _find_subscription_for_event(db: Session, data: dict) -> Subscription | None:
    """Locate the local Subscription matching a Flutterwave webhook payload."""
    subscription_obj = (
        data.get("subscription") if isinstance(data.get("subscription"), dict) else {}
    )
    sub_code = (
        data.get("subscription_code")
        or data.get("subscription_id")
        or data.get("id")
        or subscription_obj.get("id")
        or subscription_obj.get("subscription_code")
    )
    if sub_code:
        sub = (
            db.query(Subscription)
            .filter(Subscription.paystack_subscription_code == str(sub_code))
            .first()
        )
        if sub:
            return sub

    metadata = data.get("metadata") or data.get("meta") or {}
    if isinstance(metadata, dict):
        sub_id = metadata.get("subscription_id")
        if sub_id:
            sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
            if sub:
                return sub

    tx_ref = data.get("tx_ref") or data.get("reference")
    if tx_ref:
        sub_id = str(tx_ref).replace("cybercapsec-", "")
        sub = db.query(Subscription).filter(Subscription.id == sub_id).first()
        if sub:
            return sub

    customer_code = None
    if isinstance(data.get("customer"), dict):
        customer = data["customer"]
        customer_code = (
            customer.get("customer_code")
            or customer.get("id")
            or customer.get("customer_id")
        )
    if customer_code:
        company = (
            db.query(Company)
            .filter(Company.paystack_customer_code == str(customer_code))
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


def _activate_company_tier(db: Session, sub: Subscription) -> None:
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


def _provider_subscription_id(data: dict) -> str | None:
    subscription_obj = (
        data.get("subscription") if isinstance(data.get("subscription"), dict) else {}
    )
    value = (
        data.get("subscription_code")
        or data.get("subscription_id")
        or data.get("id")
        or subscription_obj.get("id")
        or subscription_obj.get("subscription_code")
    )
    return str(value) if value is not None and str(value) else None


def _provider_customer_id(data: dict) -> str | None:
    if not isinstance(data.get("customer"), dict):
        return None
    customer = data["customer"]
    value = (
        customer.get("customer_code")
        or customer.get("id")
        or customer.get("customer_id")
    )
    return str(value) if value is not None and str(value) else None


def _handle_subscription_create(db: Session, event: BillingEvent, data: dict) -> None:
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        event.processing_error = (
            "subscription create received but no matching local subscription"
        )
        return

    sub.paystack_subscription_code = _provider_subscription_id(data)
    sub.paystack_email_token = data.get("email_token")
    sub.paystack_customer_code = _provider_customer_id(data)
    sub.status = SubscriptionStatus.ACTIVE
    event.subscription_id = sub.id
    event.company_id = sub.company_id

    company = db.query(Company).filter(Company.id == sub.company_id).first()
    if company and sub.paystack_customer_code:
        company.paystack_customer_code = sub.paystack_customer_code

    _activate_company_tier(db, sub)


def _handle_charge_success(db: Session, event: BillingEvent, data: dict) -> None:
    if data.get("status") not in (None, "successful", "success", "completed"):
        return

    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return

    event.subscription_id = sub.id
    event.company_id = sub.company_id

    provider_sub_id = _provider_subscription_id(data)
    if provider_sub_id and not sub.paystack_subscription_code:
        sub.paystack_subscription_code = provider_sub_id

    provider_customer_id = _provider_customer_id(data)
    if provider_customer_id and not sub.paystack_customer_code:
        sub.paystack_customer_code = provider_customer_id

    if sub.status in (SubscriptionStatus.PENDING, SubscriptionStatus.ATTENTION):
        sub.status = SubscriptionStatus.ACTIVE
        _activate_company_tier(db, sub)


def _handle_subscription_disable(db: Session, event: BillingEvent, data: dict) -> None:
    sub = _find_subscription_for_event(db, data)
    if sub is None:
        return
    sub.status = SubscriptionStatus.CANCELLED
    sub.cancelled_at = datetime.now(timezone.utc)
    event.subscription_id = sub.id
    event.company_id = sub.company_id
    _downgrade_company_to_free(db, sub)


def _handle_subscription_not_renew(db: Session, event: BillingEvent, data: dict) -> None:
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
