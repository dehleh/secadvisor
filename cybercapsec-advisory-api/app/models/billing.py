"""Subscription and billing-related models.

Subscription
  Mirror of the Paystack subscription state for one company. We don't
  trust our local copy; webhook events from Paystack are the source of
  truth and we update Subscription rows in response.

BillingEvent
  Append-only log of every webhook we received from Paystack. Useful for
  debugging and audit trails. We never delete from this table.
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.company import BillingCurrency, SubscriptionTier
from app.models.mixins import TimestampMixin, UUIDPKMixin


class SubscriptionStatus(str, PyEnum):
    """Mirrors Paystack subscription status values plus our internal ones.

    Paystack values: active, non-renewing, attention, completed, cancelled.
    Our additions: pending (created locally, awaiting first payment).
    """
    PENDING = "pending"
    ACTIVE = "active"
    NON_RENEWING = "non_renewing"
    ATTENTION = "attention"  # payment failed, retrying
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BillingInterval(str, PyEnum):
    MONTHLY = "monthly"
    ANNUALLY = "annually"


class Subscription(Base, UUIDPKMixin, TimestampMixin):
    """One row per active subscription. A company has at most one active.

    The (company_id, status='active') uniqueness is enforced at the service
    layer rather than the schema, since cancelled subscriptions linger in
    the table for history.
    """

    __tablename__ = "subscriptions"

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Plan details — denormalized at subscription creation so historical
    # subscriptions reflect the price the customer actually paid.
    tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier), nullable=False
    )
    interval: Mapped[BillingInterval] = mapped_column(
        Enum(BillingInterval), nullable=False, default=BillingInterval.MONTHLY
    )
    currency: Mapped[BillingCurrency] = mapped_column(
        Enum(BillingCurrency), nullable=False
    )
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)  # kobo / cents

    # Paystack identifiers
    paystack_plan_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paystack_subscription_code: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    paystack_customer_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paystack_email_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # email_token is needed to call cancel-subscription on Paystack

    # State
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.PENDING,
        index=True,
    )
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Relationships
    company = relationship("Company")

    __table_args__ = (
        Index("ix_subscriptions_company_status", "company_id", "status"),
    )


class BillingEventType(str, PyEnum):
    """Paystack webhook event types we care about.

    OTHER is for events we receive but don't act on; we still log them.
    """
    CHARGE_SUCCESS = "charge.success"
    CHARGE_FAILED = "charge.failed"
    SUBSCRIPTION_CREATE = "subscription.create"
    SUBSCRIPTION_DISABLE = "subscription.disable"
    SUBSCRIPTION_NOT_RENEW = "subscription.not_renew"
    SUBSCRIPTION_EXPIRING_CARDS = "subscription.expiring_cards"
    INVOICE_CREATE = "invoice.create"
    INVOICE_UPDATE = "invoice.update"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    CUSTOMER_IDENTIFICATION_FAILED = "customeridentification.failed"
    CUSTOMER_IDENTIFICATION_SUCCESS = "customeridentification.success"
    OTHER = "other"


class BillingEvent(Base, UUIDPKMixin, TimestampMixin):
    """Append-only log of Paystack webhook events.

    Idempotency: paystack_event_id (when present) is unique. Re-deliveries
    of the same event are no-ops on the second encounter.
    """

    __tablename__ = "billing_events"

    # Paystack's event identifier (from the payload). Webhooks don't always
    # carry one in older formats so this can be null; we then dedupe via
    # signature + body hash if needed.
    paystack_event_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )

    event_type: Mapped[BillingEventType] = mapped_column(
        Enum(BillingEventType), nullable=False, index=True
    )
    raw_event_name: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Resolved at receipt time when possible
    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subscription_id: Mapped[str | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Processing state
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
