import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { asTierLimitError, UpgradePrompt } from "@/components/UpgradePrompt";

describe("asTierLimitError", () => {
  it("identifies a 402 with structured tier_limit detail", () => {
    const err = {
      message: "You've reached your evidence limit",
      status: 402,
      detail: {
        error: "tier_limit",
        limit: "max_evidence_items",
        current_tier: "starter",
        cap: 25,
        current_count: 25,
        message: "You've reached your evidence limit",
      },
    };
    const result = asTierLimitError(err);
    expect(result).not.toBeNull();
    expect(result?.current_tier).toBe("starter");
    expect(result?.limit).toBe("max_evidence_items");
  });

  it("returns null for non-402 errors", () => {
    expect(asTierLimitError({ status: 500, detail: {} })).toBeNull();
  });

  it("returns null for 402 without tier_limit detail", () => {
    expect(
      asTierLimitError({
        status: 402,
        detail: { error: "something_else" },
      }),
    ).toBeNull();
  });

  it("returns null for null/undefined", () => {
    expect(asTierLimitError(null)).toBeNull();
    expect(asTierLimitError(undefined)).toBeNull();
  });
});

describe("UpgradePrompt", () => {
  it("renders the message and a link to billing", () => {
    render(
      <MemoryRouter>
        <UpgradePrompt
          error={{
            error: "tier_limit",
            current_tier: "starter",
            message: "You've hit your Starter evidence limit.",
          }}
        />
      </MemoryRouter>,
    );
    expect(
      screen.getByText("You've hit your Starter evidence limit."),
    ).toBeInTheDocument();
    const link = screen.getByRole("link", { name: /view plans/i });
    expect(link).toHaveAttribute("href", "/billing");
  });
});
