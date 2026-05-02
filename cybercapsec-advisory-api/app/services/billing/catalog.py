"""Plan catalog — the source of truth for what tiers cost in which currencies.

Pricing is stored in minor units (kobo for NGN, cents for KES/ZAR/GHS/USD).
Adjust here, no code changes needed elsewhere — the pricing flows through
Paystack plan creation and the billing UI from this single config.

Plan codes for Paystack are populated at deploy time. Production deploys
should call `python -m app.cli sync-plans` once after seeding to upsert
plans into Paystack and capture their plan_codes.
"""
from dataclasses import dataclass

from app.models import BillingCurrency, BillingInterval, SubscriptionTier


@dataclass(frozen=True)
class PlanDefinition:
    """One row in the plan catalog. Tier × currency × interval combination."""
    tier: SubscriptionTier
    currency: BillingCurrency
    interval: BillingInterval
    amount_minor: int
    name: str
    description: str

    @property
    def amount_major(self) -> float:
        """Amount in major currency units (NGN, USD, etc) for display."""
        return self.amount_minor / 100

    @property
    def lookup_key(self) -> str:
        """Stable key for matching to a Paystack plan_code in storage."""
        return f"{self.tier.value}.{self.currency.value}.{self.interval.value}"


# ----- Plan catalog ----------------------------------------------------------
#
# Reasoning behind the pricing:
# - NGN benchmarks: a SaaS at ₦15K/mo is "I can put it on my company card without
#   asking" for a seed-stage Nigerian fintech. ₦45K/mo is "this is a real line item
#   I need to justify". ₦150K/mo is "this is on par with a junior engineer's
#   monthly cost; we're committing".
# - KES, ZAR, GHS approximate the NGN tier at local purchasing power, not just
#   FX conversion (which would price out non-Nigerian markets at parity).
# - USD is for everyone outside our four core markets — priced at the equivalent
#   of "a Vanta-lite subscription a US founder would notice but pay".

CATALOG: list[PlanDefinition] = [
    # Starter tier
    PlanDefinition(
        tier=SubscriptionTier.STARTER,
        currency=BillingCurrency.NGN,
        interval=BillingInterval.MONTHLY,
        amount_minor=15_000_00,  # ₦15,000
        name="Starter (Monthly)",
        description="Solo founder. 1 framework, 5 evidence items, 3 policies.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.STARTER,
        currency=BillingCurrency.KES,
        interval=BillingInterval.MONTHLY,
        amount_minor=1_500_00,
        name="Starter (Monthly)",
        description="Solo founder. 1 framework, 5 evidence items, 3 policies.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.STARTER,
        currency=BillingCurrency.ZAR,
        interval=BillingInterval.MONTHLY,
        amount_minor=200_00,
        name="Starter (Monthly)",
        description="Solo founder. 1 framework, 5 evidence items, 3 policies.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.STARTER,
        currency=BillingCurrency.GHS,
        interval=BillingInterval.MONTHLY,
        amount_minor=150_00,
        name="Starter (Monthly)",
        description="Solo founder. 1 framework, 5 evidence items, 3 policies.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.STARTER,
        currency=BillingCurrency.USD,
        interval=BillingInterval.MONTHLY,
        amount_minor=10_00,
        name="Starter (Monthly)",
        description="Solo founder. 1 framework, 5 evidence items, 3 policies.",
    ),
    # Growth tier
    PlanDefinition(
        tier=SubscriptionTier.GROWTH,
        currency=BillingCurrency.NGN,
        interval=BillingInterval.MONTHLY,
        amount_minor=45_000_00,
        name="Growth (Monthly)",
        description="Real compliance program. All frameworks, AI advisor, unlimited evidence.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.GROWTH,
        currency=BillingCurrency.KES,
        interval=BillingInterval.MONTHLY,
        amount_minor=4_500_00,
        name="Growth (Monthly)",
        description="Real compliance program. All frameworks, AI advisor, unlimited evidence.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.GROWTH,
        currency=BillingCurrency.ZAR,
        interval=BillingInterval.MONTHLY,
        amount_minor=600_00,
        name="Growth (Monthly)",
        description="Real compliance program. All frameworks, AI advisor, unlimited evidence.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.GROWTH,
        currency=BillingCurrency.GHS,
        interval=BillingInterval.MONTHLY,
        amount_minor=450_00,
        name="Growth (Monthly)",
        description="Real compliance program. All frameworks, AI advisor, unlimited evidence.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.GROWTH,
        currency=BillingCurrency.USD,
        interval=BillingInterval.MONTHLY,
        amount_minor=30_00,
        name="Growth (Monthly)",
        description="Real compliance program. All frameworks, AI advisor, unlimited evidence.",
    ),
    # Audit-Ready tier
    PlanDefinition(
        tier=SubscriptionTier.AUDIT_READY,
        currency=BillingCurrency.NGN,
        interval=BillingInterval.MONTHLY,
        amount_minor=150_000_00,
        name="Audit-Ready (Monthly)",
        description="Growth + dedicated reviewer, audit prep workshop, custom drafting.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.AUDIT_READY,
        currency=BillingCurrency.KES,
        interval=BillingInterval.MONTHLY,
        amount_minor=15_000_00,
        name="Audit-Ready (Monthly)",
        description="Growth + dedicated reviewer, audit prep workshop, custom drafting.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.AUDIT_READY,
        currency=BillingCurrency.ZAR,
        interval=BillingInterval.MONTHLY,
        amount_minor=2_000_00,
        name="Audit-Ready (Monthly)",
        description="Growth + dedicated reviewer, audit prep workshop, custom drafting.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.AUDIT_READY,
        currency=BillingCurrency.GHS,
        interval=BillingInterval.MONTHLY,
        amount_minor=1_500_00,
        name="Audit-Ready (Monthly)",
        description="Growth + dedicated reviewer, audit prep workshop, custom drafting.",
    ),
    PlanDefinition(
        tier=SubscriptionTier.AUDIT_READY,
        currency=BillingCurrency.USD,
        interval=BillingInterval.MONTHLY,
        amount_minor=100_00,
        name="Audit-Ready (Monthly)",
        description="Growth + dedicated reviewer, audit prep workshop, custom drafting.",
    ),
]


def get_plan(
    tier: SubscriptionTier,
    currency: BillingCurrency,
    interval: BillingInterval = BillingInterval.MONTHLY,
) -> PlanDefinition | None:
    """Return the plan matching tier+currency+interval, or None."""
    for plan in CATALOG:
        if (
            plan.tier == tier
            and plan.currency == currency
            and plan.interval == interval
        ):
            return plan
    return None


def plans_for_currency(
    currency: BillingCurrency,
    interval: BillingInterval = BillingInterval.MONTHLY,
) -> list[PlanDefinition]:
    """All paid plans available in a given currency. Free is not in the catalog."""
    return [
        p
        for p in CATALOG
        if p.currency == currency and p.interval == interval
    ]
