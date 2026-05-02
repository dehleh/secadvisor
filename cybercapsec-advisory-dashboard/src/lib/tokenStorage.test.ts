import { afterEach, describe, expect, it } from "vitest";

import { tokenStorage } from "@/lib/tokenStorage";

describe("tokenStorage", () => {
  afterEach(() => {
    tokenStorage.clear();
  });

  it("returns null when nothing is stored", () => {
    expect(tokenStorage.getAccess()).toBeNull();
    expect(tokenStorage.getRefresh()).toBeNull();
    expect(tokenStorage.hasTokens()).toBe(false);
  });

  it("persists access and refresh tokens", () => {
    tokenStorage.set({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 3600,
    });
    expect(tokenStorage.getAccess()).toBe("a");
    expect(tokenStorage.getRefresh()).toBe("r");
    expect(tokenStorage.hasTokens()).toBe(true);
  });

  it("clears both tokens", () => {
    tokenStorage.set({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 3600,
    });
    tokenStorage.clear();
    expect(tokenStorage.hasTokens()).toBe(false);
  });
});
