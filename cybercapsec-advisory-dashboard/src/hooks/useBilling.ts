import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { billingApi } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { SubscriptionTierCode } from "@/types/api";

export function usePricing() {
  return useQuery({
    queryKey: queryKeys.billing.pricing,
    queryFn: () => billingApi.pricing(),
    // Pricing rarely changes within a session; cache for an hour
    staleTime: 1000 * 60 * 60,
  });
}

export function useCurrentSubscription() {
  return useQuery({
    queryKey: queryKeys.billing.subscription,
    queryFn: () => billingApi.subscription(),
  });
}

export function useStartCheckout() {
  return useMutation({
    mutationFn: ({
      tier,
      callbackUrl,
    }: {
      tier: SubscriptionTierCode;
      callbackUrl?: string;
    }) => billingApi.checkout(tier, callbackUrl),
  });
}

export function useCancelSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => billingApi.cancel(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.billing.subscription });
    },
  });
}
