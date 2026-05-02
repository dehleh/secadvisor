import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import { AuthProvider, useAuth } from "@/context/AuthContext";
import { tokenStorage } from "@/lib/tokenStorage";
import { authApi } from "@/api";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Test component that surfaces auth state
function AuthSpy() {
  const { user, isAuthenticated, isLoading } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authed">{String(isAuthenticated)}</span>
      <span data-testid="user">{user?.email ?? "none"}</span>
    </div>
  );
}

function renderAuth() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <AuthSpy />
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    tokenStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    tokenStorage.clear();
  });

  it("starts unauthenticated when no tokens are present", async () => {
    renderAuth();
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(screen.getByTestId("authed").textContent).toBe("false");
    expect(screen.getByTestId("user").textContent).toBe("none");
  });

  it("hydrates the user when tokens are present", async () => {
    tokenStorage.set({
      access_token: "a",
      refresh_token: "r",
      token_type: "bearer",
      expires_in: 3600,
    });
    const meSpy = vi.spyOn(authApi, "me").mockResolvedValue({
      id: "u1",
      email: "u@x.ng",
      full_name: "U",
      job_title: null,
      role: "owner",
      company_id: "c1",
      is_active: true,
      is_verified: false,
    });

    renderAuth();
    await waitFor(() =>
      expect(screen.getByTestId("authed").textContent).toBe("true"),
    );
    expect(screen.getByTestId("user").textContent).toBe("u@x.ng");
    expect(meSpy).toHaveBeenCalled();
  });

  it("clears tokens when /auth/me fails", async () => {
    tokenStorage.set({
      access_token: "bad",
      refresh_token: "bad",
      token_type: "bearer",
      expires_in: 3600,
    });
    vi.spyOn(authApi, "me").mockRejectedValue(new Error("401"));

    renderAuth();
    await waitFor(() =>
      expect(screen.getByTestId("authed").textContent).toBe("false"),
    );
    expect(tokenStorage.hasTokens()).toBe(false);
  });

  it("login persists tokens and sets user", async () => {
    vi.spyOn(authApi, "login").mockResolvedValue({
      access_token: "new-a",
      refresh_token: "new-r",
      token_type: "bearer",
      expires_in: 3600,
    });
    vi.spyOn(authApi, "me").mockResolvedValue({
      id: "u1",
      email: "x@y.ng",
      full_name: "X",
      job_title: null,
      role: "owner",
      company_id: "c1",
      is_active: true,
      is_verified: true,
    });

    function LoginButton() {
      const { login } = useAuth();
      return (
        <button
          onClick={() => void login({ email: "x@y.ng", password: "Strong!" })}
        >
          go
        </button>
      );
    }

    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={qc}>
        <AuthProvider>
          <LoginButton />
          <AuthSpy />
        </AuthProvider>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );

    await act(async () => {
      screen.getByText("go").click();
    });

    await waitFor(() =>
      expect(screen.getByTestId("user").textContent).toBe("x@y.ng"),
    );
    expect(tokenStorage.getAccess()).toBe("new-a");
  });
});
