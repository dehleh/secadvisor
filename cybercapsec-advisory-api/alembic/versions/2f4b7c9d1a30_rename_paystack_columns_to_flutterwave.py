"""rename paystack columns to flutterwave

Revision ID: 2f4b7c9d1a30
Revises: 8c3d2f1a9b77
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2f4b7c9d1a30"
down_revision: Union[str, None] = "8c3d2f1a9b77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_subscriptions_paystack_subscription_code", table_name="subscriptions")
    op.drop_index("ix_billing_events_paystack_event_id", table_name="billing_events")

    op.alter_column(
        "companies",
        "paystack_customer_code",
        new_column_name="flutterwave_customer_code",
    )
    op.alter_column(
        "companies",
        "paystack_subscription_code",
        new_column_name="flutterwave_subscription_code",
    )

    op.alter_column(
        "subscriptions",
        "paystack_plan_code",
        new_column_name="flutterwave_plan_code",
    )
    op.alter_column(
        "subscriptions",
        "paystack_subscription_code",
        new_column_name="flutterwave_subscription_code",
    )
    op.alter_column(
        "subscriptions",
        "paystack_customer_code",
        new_column_name="flutterwave_customer_code",
    )
    op.alter_column(
        "subscriptions",
        "paystack_email_token",
        new_column_name="flutterwave_email_token",
    )

    op.alter_column(
        "billing_events",
        "paystack_event_id",
        new_column_name="flutterwave_event_id",
    )

    op.create_index(
        "ix_subscriptions_flutterwave_subscription_code",
        "subscriptions",
        ["flutterwave_subscription_code"],
        unique=False,
    )
    op.create_index(
        "ix_billing_events_flutterwave_event_id",
        "billing_events",
        ["flutterwave_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_events_flutterwave_event_id",
        table_name="billing_events",
    )
    op.drop_index(
        "ix_subscriptions_flutterwave_subscription_code",
        table_name="subscriptions",
    )

    op.alter_column(
        "billing_events",
        "flutterwave_event_id",
        new_column_name="paystack_event_id",
    )

    op.alter_column(
        "subscriptions",
        "flutterwave_email_token",
        new_column_name="paystack_email_token",
    )
    op.alter_column(
        "subscriptions",
        "flutterwave_customer_code",
        new_column_name="paystack_customer_code",
    )
    op.alter_column(
        "subscriptions",
        "flutterwave_subscription_code",
        new_column_name="paystack_subscription_code",
    )
    op.alter_column(
        "subscriptions",
        "flutterwave_plan_code",
        new_column_name="paystack_plan_code",
    )

    op.alter_column(
        "companies",
        "flutterwave_subscription_code",
        new_column_name="paystack_subscription_code",
    )
    op.alter_column(
        "companies",
        "flutterwave_customer_code",
        new_column_name="paystack_customer_code",
    )

    op.create_index(
        "ix_billing_events_paystack_event_id",
        "billing_events",
        ["paystack_event_id"],
        unique=True,
    )
    op.create_index(
        "ix_subscriptions_paystack_subscription_code",
        "subscriptions",
        ["paystack_subscription_code"],
        unique=False,
    )
