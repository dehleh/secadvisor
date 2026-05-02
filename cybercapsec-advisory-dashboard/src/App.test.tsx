import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { App } from "@/App";
import { AuthProvider } from "@/context/AuthContext";
import { tokenStorage } from "@/lib/tokenStorage";

function renderApp(route: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App routing & auth guards", () => {
  beforeEach(() => {
    tokenStorage.clear();
    // Mock fetch / axios behavior — we just need /auth/me to fail when no token
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({}), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("unauthenticated user hitting /dashboard is redirected to /login", async () => {
    renderApp("/dashboard");
    expect(
      await screen.findByRole("heading", { name: /CyberCapSec Advisory/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Sign in/i })).toBeInTheDocument();
  });

  it("unauthenticated user hitting / falls back to login via /dashboard guard", async () => {
    renderApp("/");
    expect(
      await screen.findByRole("button", { name: /Sign in/i }),
    ).toBeInTheDocument();
  });

  it("/login renders the login form", async () => {
    renderApp("/login");
    expect(
      await screen.findByRole("button", { name: /Sign in/i }),
    ).toBeInTheDocument();
  });

  it("/signup renders the signup form", async () => {
    renderApp("/signup");
    expect(
      await screen.findByRole("button", { name: /Create account/i }),
    ).toBeInTheDocument();
  });
});
