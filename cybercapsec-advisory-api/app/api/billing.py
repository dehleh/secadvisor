"""Billing API endpoints - Flutterwave-backed.

  GET    /billing/pricing         pricing for the company's currency
  GET    /billing/subscription    current subscription state
  POST   /billing/checkout        start checkout flow, returns auth URL
  POST   /billing/cancel          cancel current subscription
  POST   /billing/webhook         Flutterwave webhook receiver (public, signed)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_company, get_current_user
from app.models import (
    BillingCurrency,
    Company,
    Subscription,
    SubscriptionStatus,
    SubscriptionTier,
    User,
)
from app.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    CurrentSubscriptionOut,
    PlanOut,
    PricingOut,
    SubscriptionOut,
)
from app.services.billing import (
    FlutterwaveClientBase,
    cancel_subscription,
    get_flutterwave_client,
    plans_for_currency,
    process_webhook_event,
    record_event,
    start_checkout,
    verify_flutterwave_signature,
)
from app.services.billing.limits import TIER_LIMITS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


def get_billing_client() -> FlutterwaveClientBase:
    settings = get_settings()
    return get_flutterwave_client(
        use_mock=settings.USE_MOCK_PAYMENTS,
        secret_key=settings.FLUTTERWAVE_SECRET_KEY or None,
    )


def _plan_to_out(plan, limits) -> PlanOut:
    return PlanOut(
        tier=plan.tier,
        name=plan.name,
        description=plan.description,
        interval=plan.interval,
        currency=plan.currency,
        amount_minor=plan.amount_minor,
        amount_major=plan.amount_major,
        max_active_assessments=limits.max_active_assessments,
        max_evidence_items=limits.max_evidence_items,
        max_published_policies=limits.max_published_policies,
        max_frameworks=limits.max_frameworks,
        ai_advisor_enabled=limits.ai_advisor_enabled,
        custom_policy_drafting=limits.custom_policy_drafting,
        dedicated_reviewer=limits.dedicated_reviewer,
    )


def _free_plan_out(currency: BillingCurrency) -> PlanOut:
    from app.models import BillingInterval

    limits = TIER_LIMITS[SubscriptionTier.FREE]
    return PlanOut(
        tier=SubscriptionTier.FREE,
        name="Free preview",
        description=(
            "Create an account, view pricing, and purchase a licence. "
            "Workspace access starts on a paid plan."
        ),
        interval=BillingInterval.MONTHLY,
        currency=currency,
        amount_minor=0,
        amount_major=0,
        max_active_assessments=limits.max_active_assessments,
        max_evidence_items=limits.max_evidence_items,
        max_published_policies=limits.max_published_policies,
        max_frameworks=limits.max_frameworks,
        ai_advisor_enabled=limits.ai_advisor_enabled,
        custom_policy_drafting=limits.custom_policy_drafting,
        dedicated_reviewer=limits.dedicated_reviewer,
    )


@router.get(
    "/pricing",
    response_model=PricingOut,
    summary="Pricing for the current company's currency",
)
def pricing(company: Annotated[Company, Depends(get_current_company)]) -> PricingOut:
    paid = []
    for plan in plans_for_currency(company.billing_currency):
        paid.append(_plan_to_out(plan, TIER_LIMITS[plan.tier]))
    return PricingOut(
        currency=company.billing_currency,
        free=_free_plan_out(company.billing_currency),
        paid=paid,
    )


@router.get(
    "/subscription",
    response_model=CurrentSubscriptionOut,
    summary="Current subscription state for the company",
)
def current_subscription(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentSubscriptionOut:
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.company_id == company.id,
            Subscription.status.in_(
                [
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.NON_RENEWING,
                    SubscriptionStatus.ATTENTION,
                    SubscriptionStatus.PENDING,
                ]
            ),
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    return CurrentSubscriptionOut(
        tier=company.subscription_tier,
        currency=company.billing_currency,
        active_subscription=SubscriptionOut.model_validate(sub) if sub else None,
    )


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a checkout flow for a tier upgrade",
)
def checkout(
    payload: CheckoutRequest,
    company: Annotated[Company, Depends(get_current_company)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    flutterwave: Annotated[FlutterwaveClientBase, Depends(get_billing_client)],
) -> CheckoutResponse:
    settings = get_settings()
    callback_url = (
        payload.callback_url
        or settings.FLUTTERWAVE_CHECKOUT_CALLBACK_URL
    )

    sub, init = start_checkout(
        db,
        company=company,
        user_email=user.email,
        tier=payload.tier,
        callback_url=callback_url,
        flutterwave_client=flutterwave,
        plan_code_env=dict(os.environ),
    )
    return CheckoutResponse(
        subscription_id=sub.id,
        authorization_url=init.authorization_url,
        reference=init.reference,
    )


@router.post(
    "/cancel",
    response_model=SubscriptionOut,
    summary="Cancel the current subscription",
)
def cancel(
    company: Annotated[Company, Depends(get_current_company)],
    db: Annotated[Session, Depends(get_db)],
    flutterwave: Annotated[FlutterwaveClientBase, Depends(get_billing_client)],
) -> SubscriptionOut:
    sub = cancel_subscription(
        db,
        company=company,
        flutterwave_client=flutterwave,
    )
    return SubscriptionOut.model_validate(sub)


@router.post(
    "/webhook",
    summary="Flutterwave webhook receiver (public; HMAC-SHA256 signed)",
    status_code=status.HTTP_200_OK,
)
async def flutterwave_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("flutterwave-signature")
    secret_hash = settings.FLUTTERWAVE_SECRET_HASH

    if not verify_flutterwave_signature(
        raw_body=raw_body,
        signature_header=signature,
        secret_hash=secret_hash,
    ):
        logger.warning(
            "Rejected Flutterwave webhook with invalid signature (path=%s)",
            request.url.path,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON",
        )

    event_name = payload.get("event") or payload.get("type")
    if not event_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type",
        )

    data = payload.get("data") or {}
    event_id = None
    if isinstance(data, dict):
        event_id = f"{event_name}:{payload.get('webhook_id') or payload.get('id') or data.get('id') or data.get('tx_ref') or data.get('reference') or data.get('subscription_code') or data.get('subscription_id') or ''}"

    event = record_event(
        db,
        event_name=event_name,
        payload=payload,
        provider_event_id=event_id,
    )
    if event is None:
        return {"status": "duplicate"}

    try:
        process_webhook_event(db, event=event)
    except Exception as exc:
        logger.exception("Webhook handler failed for event %s", event_name)
        event.processing_error = str(exc)[:1000]

    db.commit()
    return {"status": "ok"}
