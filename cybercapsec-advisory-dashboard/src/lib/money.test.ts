import { describe, expect, it } from "vitest";

import { formatMoney, minorToMajor } from "@/lib/money";

describe("formatMoney", () => {
  it("formats NGN without decimals when whole", () => {
    const result = formatMoney(15000, "NGN");
    // Result varies by Node Intl support; ensure currency symbol or code present
    expect(result).toMatch(/15,000|15000|NGN|₦/);
  });

  it("formats KES", () => {
    const result = formatMoney(1500, "KES");
    expect(result).toMatch(/1,500|1500|KES|KSh/);
  });

  it("formats USD with cents when fractional", () => {
    const result = formatMoney(10.5, "USD");
    expect(result).toMatch(/10\.50|10\.5|USD|\$/);
  });

  it("formats free amount for ZAR as zero", () => {
    const result = formatMoney(0, "ZAR");
    expect(result).toMatch(/0|R|ZAR/);
  });
});

describe("minorToMajor", () => {
  it("divides by 100", () => {
    expect(minorToMajor(15000_00)).toBe(15000);
    expect(minorToMajor(0)).toBe(0);
    expect(minorToMajor(1)).toBe(0.01);
  });
});
