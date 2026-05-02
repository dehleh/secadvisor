import type { BillingCurrency } from "@/types/api";

const CURRENCY_LOCALES: Record<BillingCurrency, string> = {
  NGN: "en-NG",
  KES: "en-KE",
  ZAR: "en-ZA",
  GHS: "en-GH",
  USD: "en-US",
};

const CURRENCY_SYMBOLS: Record<BillingCurrency, string> = {
  NGN: "₦",
  KES: "KSh",
  ZAR: "R",
  GHS: "₵",
  USD: "$",
};

/**
 * Format a major-unit amount (e.g. 15000 for ₦15,000) for display.
 * Uses Intl.NumberFormat with the appropriate locale; falls back to a
 * symbol + formatted number if the runtime doesn't support a locale.
 */
export function formatMoney(
  amountMajor: number,
  currency: BillingCurrency,
): string {
  try {
    return new Intl.NumberFormat(CURRENCY_LOCALES[currency], {
      style: "currency",
      currency,
      maximumFractionDigits: amountMajor % 1 === 0 ? 0 : 2,
    }).format(amountMajor);
  } catch {
    return `${CURRENCY_SYMBOLS[currency]}${amountMajor.toLocaleString()}`;
  }
}

/**
 * Format a "free" plan price.
 */
export function formatFreePrice(): string {
  return "Free";
}

/**
 * Convert minor units (kobo, cents) to major units (NGN, USD).
 */
export function minorToMajor(minor: number): number {
  return minor / 100;
}
