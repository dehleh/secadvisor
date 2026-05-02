import { apiClient } from "@/api/client";
import type {
  CheckoutResponse,
  CurrentSubscriptionOut,
  PricingOut,
  SubscriptionOut,
  SubscriptionTierCode,
} from "@/types/api";

export const billingApi = {
  pricing: async (): Promise<PricingOut> => {
    const { data } = await apiClient.get<PricingOut>("/billing/pricing");
    return data;
  },

  subscription: async (): Promise<CurrentSubscriptionOut> => {
    const { data } = await apiClient.get<CurrentSubscriptionOut>(
      "/billing/subscription",
    );
    return data;
  },

  checkout: async (
    tier: SubscriptionTierCode,
    callbackUrl?: string,
  ): Promise<CheckoutResponse> => {
    const { data } = await apiClient.post<CheckoutResponse>(
      "/billing/checkout",
      { tier, callback_url: callbackUrl },
    );
    return data;
  },

  cancel: async (): Promise<SubscriptionOut> => {
    const { data } = await apiClient.post<SubscriptionOut>("/billing/cancel");
    return data;
  },
};
