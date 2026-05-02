import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";

import type { ApiError, TierLimitError } from "@/types/api";

/**
 * Detect whether an API error is a tier-limit hit (402 with a structured
 * detail). Returns the parsed shape or null.
 */
export function asTierLimitError(error: unknown): TierLimitError | null {
  if (!error || typeof error !== "object") return null;
  const apiError = error as ApiError;
  if (apiError.status !== 402) return null;
  const detail = apiError.detail;
  if (!detail || typeof detail !== "object") return null;
  const candidate = detail as Record<string, unknown>;
  if (candidate.error !== "tier_limit") return null;
  return candidate as unknown as TierLimitError;
}

interface UpgradePromptProps {
  error: TierLimitError;
  className?: string;
}

/**
 * Friendly upgrade prompt shown in place of a generic error when the user
 * hits a tier limit. Always links to /billing.
 */
export function UpgradePrompt({ error, className }: UpgradePromptProps) {
  return (
    <div
      className={
        "rounded-lg border border-brand-200 bg-brand-50 p-4 " + (className ?? "")
      }
    >
      <div className="flex items-start gap-3">
        <Sparkles className="h-5 w-5 text-brand-600 mt-0.5 shrink-0" />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-brand-900">
            Time to upgrade
          </h3>
          <p className="text-sm text-brand-800 mt-1">{error.message}</p>
          <Link
            to="/billing"
            className="inline-block mt-3 text-sm font-medium text-brand-700 hover:text-brand-900 underline"
          >
            View plans →
          </Link>
        </div>
      </div>
    </div>
  );
}
