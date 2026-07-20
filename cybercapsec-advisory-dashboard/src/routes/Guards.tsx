import { type ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";
import { ErrorMessage, LoadingPage } from "@/components/UI";
import { useCurrentSubscription } from "@/hooks/useBilling";
import { normalizeApiError } from "@/api";
import type { SubscriptionTierCode } from "@/types/api";

const PAID_TIERS = new Set<SubscriptionTierCode>([
  "starter",
  "growth",
  "audit_ready",
]);

export function hasPaidLicense(tier: SubscriptionTierCode | null | undefined) {
  return tier ? PAID_TIERS.has(tier) : false;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <LoadingPage />;
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

export function RequirePaidLicense({ children }: { children: ReactNode }) {
  const location = useLocation();
  const subscriptionQuery = useCurrentSubscription();

  if (subscriptionQuery.isLoading) return <LoadingPage />;
  if (subscriptionQuery.error) {
    return (
      <ErrorMessage message={normalizeApiError(subscriptionQuery.error).message} />
    );
  }

  const tier = subscriptionQuery.data?.tier;
  if (!hasPaidLicense(tier)) {
    return (
      <Navigate
        to="/billing"
        state={{ from: location.pathname, reason: "license_required" }}
        replace
      />
    );
  }

  return <>{children}</>;
}

export function RequireGuest({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingPage />;
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return <>{children}</>;
}
