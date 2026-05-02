// Authentication context. Owns:
//   - the current User (or null)
//   - login / signup / logout actions
//   - hydration on mount: if tokens are in storage, attempt /auth/me
//
// Server state (TanStack Query) and auth state (this context) live side
// by side. Auth changes invalidate the entire query cache because the
// previous user's data must not leak into a new session.

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { authApi } from "@/api";
import { tokenStorage } from "@/lib/tokenStorage";
import type {
  AuthTokens,
  LoginPayload,
  SignupPayload,
  User,
} from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const queryClient = useQueryClient();

  const hydrate = useCallback(async () => {
    if (!tokenStorage.hasTokens()) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      // /auth/me failed despite having tokens — clear and stay logged out
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const finalizeAuth = useCallback(
    async (tokens: AuthTokens) => {
      tokenStorage.set(tokens);
      const me = await authApi.me();
      setUser(me);
      // Wipe any cached state from a previous session
      queryClient.clear();
    },
    [queryClient],
  );

  const login = useCallback(
    async (payload: LoginPayload) => {
      const tokens = await authApi.login(payload);
      await finalizeAuth(tokens);
    },
    [finalizeAuth],
  );

  const signup = useCallback(
    async (payload: SignupPayload) => {
      const response = await authApi.signup(payload);
      tokenStorage.set(response.tokens);
      setUser(response.user);
      queryClient.clear();
    },
    [queryClient],
  );

  const logout = useCallback(() => {
    tokenStorage.clear();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  const refresh = useCallback(async () => {
    const me = await authApi.me();
    setUser(me);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      signup,
      logout,
      refresh,
    }),
    [user, isLoading, login, signup, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
