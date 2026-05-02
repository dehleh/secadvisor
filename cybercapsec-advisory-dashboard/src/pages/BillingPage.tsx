import { useEffect, useState } from "react";
import { Check, ExternalLink, X } from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  ErrorMessage,
  LoadingPage,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import {
  useCancelSubscription,
  useCurrentSubscription,
  usePricing,
  useStartCheckout,
} from "@/hooks/useBilling";
import { formatMoney } from "@/lib/money";
import type { PlanOut, SubscriptionTierCode } from "@/types/api";

const TIER_ORDER: SubscriptionTierCode[] = [
  "free",
  "starter",
  "growth",
  "audit_ready",
];

function tierRank(tier: SubscriptionTierCode): number {
  return TIER_ORDER.indexOf(tier);
}

interface PlanFeatureProps {
  included: boolean;
  children: React.ReactNode;
}

function PlanFeature({ included, children }: PlanFeatureProps) {
  return (
    <li className="flex items-start gap-2 text-sm">
      {included ? (
        <Check className="h-4 w-4 mt-0.5 text-emerald-500 shrink-0" />
      ) : (
        <X className="h-4 w-4 mt-0.5 text-slate-300 shrink-0" />
      )}
      <span className={included ? "text-slate-700" : "text-slate-400"}>
        {children}
      </span>
    </li>
  );
}

interface PlanCardProps {
  plan: PlanOut;
  currentTier: SubscriptionTierCode;
  onSelect: (tier: SubscriptionTierCode) => void;
  isCheckoutLoading: boolean;
  pendingTier: SubscriptionTierCode | null;
}

function PlanCard({
  plan,
  currentTier,
  onSelect,
  isCheckoutLoading,
  pendingTier,
}: PlanCardProps) {
  const isCurrent = plan.tier === currentTier;
  const isUpgrade = tierRank(plan.tier) > tierRank(currentTier);
  const isDowngrade = tierRank(plan.tier) < tierRank(currentTier);
  const isPending = pendingTier === plan.tier && isCheckoutLoading;

  const cap = (n: number | null, label: string) =>
    n === null ? `Unlimited ${label}` : `Up to ${n} ${label}`;

  // Highlight Growth — that's the price-anchor / recommended tier
  const isHighlighted = plan.tier === "growth" && !isCurrent;

  return (
    <Card
      className={
        isHighlighted
          ? "border-brand-500 shadow-md ring-1 ring-brand-500"
          : isCurrent
            ? "border-emerald-500"
            : ""
      }
    >
      {isHighlighted && (
        <div className="bg-brand-600 text-white text-xs font-semibold uppercase tracking-wide text-center py-1.5 rounded-t-lg">
          Most popular
        </div>
      )}
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle>{plan.name.replace(/ \(Monthly\)/, "")}</CardTitle>
          {isCurrent && <Badge variant="success">Current</Badge>}
        </div>
        <p className="text-sm text-slate-600 mt-1 min-h-[2.5rem]">
          {plan.description}
        </p>
      </CardHeader>
      <CardBody>
        <div className="mb-4">
          {plan.amount_minor === 0 ? (
            <div>
              <span className="text-3xl font-bold text-slate-900">Free</span>
              <span className="text-sm text-slate-500 ml-1">forever</span>
            </div>
          ) : (
            <div>
              <span className="text-3xl font-bold text-slate-900">
                {formatMoney(plan.amount_major, plan.currency)}
              </span>
              <span className="text-sm text-slate-500 ml-1">/month</span>
            </div>
          )}
        </div>

        <ul className="space-y-2 mb-5 min-h-[12rem]">
          <PlanFeature included>
            {cap(plan.max_active_assessments, "active assessments")}
          </PlanFeature>
          <PlanFeature included>
            {cap(plan.max_evidence_items, "evidence items")}
          </PlanFeature>
          <PlanFeature included>
            {cap(plan.max_published_policies, "published policies")}
          </PlanFeature>
          <PlanFeature included>
            {plan.max_frameworks === null
              ? "All frameworks (SOC 2, NDPA, CBN, ISO 27001, POPIA, Kenya DPA)"
              : `${plan.max_frameworks} frameworks`}
          </PlanFeature>
          <PlanFeature included={plan.ai_advisor_enabled}>
            AI advisor (Claude-powered)
          </PlanFeature>
          <PlanFeature included={plan.custom_policy_drafting}>
            Custom policy drafting
          </PlanFeature>
          <PlanFeature included={plan.dedicated_reviewer}>
            Dedicated reviewer
          </PlanFeature>
        </ul>

        {isCurrent ? (
          <Button variant="outline" className="w-full" disabled>
            Current plan
          </Button>
        ) : plan.tier === "free" ? (
          isDowngrade ? (
            <Button
              variant="outline"
              className="w-full"
              disabled
              title="Cancel your subscription to downgrade to free"
            >
              Cancel subscription to downgrade
            </Button>
          ) : (
            <Button variant="outline" className="w-full" disabled>
              Free
            </Button>
          )
        ) : (
          <Button
            variant={isHighlighted ? "primary" : "outline"}
            className="w-full"
            loading={isPending}
            disabled={isCheckoutLoading && !isPending}
            onClick={() => onSelect(plan.tier)}
          >
            {isUpgrade ? "Upgrade" : "Switch"} to{" "}
            {plan.name.replace(/ \(Monthly\)/, "")}
          </Button>
        )}
      </CardBody>
    </Card>
  );
}

export function BillingPage() {
  const pricingQuery = usePricing();
  const subscriptionQuery = useCurrentSubscription();
  const checkout = useStartCheckout();
  const cancel = useCancelSubscription();

  const [error, setError] = useState<string | null>(null);
  const [pendingTier, setPendingTier] =
    useState<SubscriptionTierCode | null>(null);

  // If the user came back from Paystack via the callback URL, refresh state.
  // Webhook is the source of truth, but a refresh sees the updated tier
  // soon after.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("reference") || params.has("trxref")) {
      void subscriptionQuery.refetch();
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (pricingQuery.isLoading || subscriptionQuery.isLoading) {
    return <LoadingPage />;
  }

  const pricingError = pricingQuery.error || subscriptionQuery.error;
  if (pricingError) {
    return <ErrorMessage message={normalizeApiError(pricingError).message} />;
  }

  const pricing = pricingQuery.data!;
  const subscription = subscriptionQuery.data!;
  const currentTier = subscription.tier;
  const activeSub = subscription.active_subscription;

  const handleSelect = async (tier: SubscriptionTierCode) => {
    setError(null);
    setPendingTier(tier);
    try {
      const callback = `${window.location.origin}/billing/return`;
      const result = await checkout.mutateAsync({
        tier,
        callbackUrl: callback,
      });
      // Redirect to Paystack
      window.location.href = result.authorization_url;
    } catch (err) {
      setError(normalizeApiError(err).message);
      setPendingTier(null);
    }
  };

  const handleCancel = async () => {
    if (
      !window.confirm(
        "Cancel your subscription? You'll keep access until the end of your current billing period.",
      )
    ) {
      return;
    }
    setError(null);
    try {
      await cancel.mutateAsync();
    } catch (err) {
      setError(normalizeApiError(err).message);
    }
  };

  const allPlans = [pricing.free, ...pricing.paid];

  return (
    <>
      <PageHeader
        title="Billing & Plans"
        description={`Pricing in ${pricing.currency}. All plans bill monthly. Cancel anytime.`}
      />

      {error && (
        <div className="mb-4">
          <ErrorMessage message={error} />
        </div>
      )}

      {/* Current subscription summary */}
      {activeSub && currentTier !== "free" && (
        <Card className="mb-6">
          <CardBody className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <div className="text-sm text-slate-500 mb-1">
                Current subscription
              </div>
              <div className="flex items-center gap-2">
                <span className="text-lg font-semibold text-slate-900 capitalize">
                  {currentTier.replace("_", " ")}
                </span>
                <Badge
                  variant={
                    activeSub.status === "active"
                      ? "success"
                      : activeSub.status === "non_renewing"
                        ? "warning"
                        : activeSub.status === "attention"
                          ? "danger"
                          : "neutral"
                  }
                >
                  {activeSub.status.replace("_", " ")}
                </Badge>
              </div>
              {activeSub.cancel_at_period_end && (
                <p className="text-sm text-amber-700 mt-1">
                  Will not renew. Access continues to the end of the current
                  period.
                </p>
              )}
            </div>
            {!activeSub.cancel_at_period_end && (
              <Button
                variant="outline"
                onClick={handleCancel}
                loading={cancel.isPending}
              >
                Cancel subscription
              </Button>
            )}
          </CardBody>
        </Card>
      )}

      {/* Plans grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {allPlans.map((plan) => (
          <PlanCard
            key={plan.tier}
            plan={plan}
            currentTier={currentTier}
            onSelect={handleSelect}
            isCheckoutLoading={checkout.isPending}
            pendingTier={pendingTier}
          />
        ))}
      </div>

      <Card>
        <CardBody className="text-sm text-slate-600 space-y-2">
          <p className="font-medium text-slate-900">Payment methods</p>
          <p>
            Payments are processed securely via{" "}
            <a
              href="https://paystack.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 hover:underline inline-flex items-center gap-1"
            >
              Paystack
              <ExternalLink className="h-3 w-3" />
            </a>
            . We accept cards, bank transfers, and (in supported regions) mobile
            money. We never see or store your card details.
          </p>
          <p>
            You'll be redirected to Paystack to complete payment. After payment
            you'll be returned here automatically.
          </p>
        </CardBody>
      </Card>
    </>
  );
}
