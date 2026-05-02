import { describe, expect, it } from "vitest";

import { cn } from "@/lib/cn";

describe("cn", () => {
  it("joins truthy class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("filters out falsy values", () => {
    expect(cn("a", null, undefined, false, "b")).toBe("a b");
  });

  it("merges conflicting tailwind classes (last wins)", () => {
    // tailwind-merge resolves conflicts within the same property
    expect(cn("p-2", "p-4")).toBe("p-4");
  });
});
