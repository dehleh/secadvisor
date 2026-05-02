// Token persistence in localStorage. Tokens are short-lived; if someone
// extracts them from a stolen device, the refresh token is revoked on
// next login.

import type { AuthTokens } from "@/types/api";

const ACCESS_KEY = "ccs.access_token";
const REFRESH_KEY = "ccs.refresh_token";

export const tokenStorage = {
  getAccess(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  getRefresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: AuthTokens): void {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  hasTokens(): boolean {
    return !!(localStorage.getItem(ACCESS_KEY) && localStorage.getItem(REFRESH_KEY));
  },
};
