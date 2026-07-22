// Axios instance with auth header injection and 401 -> refresh -> retry
// flow. On refresh failure, tokens are cleared and the user is redirected
// to /login.

import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import { tokenStorage } from "@/lib/tokenStorage";
import type { AuthTokens } from "@/types/api";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    "Content-Type": "application/json",
  },
});

// ----- Auth header injection -------------------------------------------------

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ----- 401 -> refresh -> retry -----------------------------------------------

interface RetryQueueItem {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}

let isRefreshing = false;
let refreshQueue: RetryQueueItem[] = [];

const flushQueue = (token: string | null, error: unknown = null) => {
  refreshQueue.forEach((item) => {
    if (token) item.resolve(token);
    else item.reject(error);
  });
  refreshQueue = [];
};

const onAuthFailure = () => {
  tokenStorage.clear();
  // Bare redirect — outside the React tree we can't use the router. The
  // login page renders, the user re-auths, and TanStack Query state is
  // wiped on remount so no stale data persists.
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retried?: boolean })
      | undefined;

    if (
      !originalRequest ||
      error.response?.status !== 401 ||
      originalRequest._retried ||
      // Don't try to refresh during refresh itself, or during login
      originalRequest.url?.includes("/auth/refresh") ||
      originalRequest.url?.includes("/auth/login") ||
      originalRequest.url?.includes("/auth/signup")
    ) {
      return Promise.reject(error);
    }

    const refreshToken = tokenStorage.getRefresh();
    if (!refreshToken) {
      onAuthFailure();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Queue this request until the in-flight refresh completes.
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            originalRequest._retried = true;
            resolve(apiClient(originalRequest));
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    try {
      const { data } = await axios.post<AuthTokens>(
        `${API_URL}${API_PREFIX}/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json" } },
      );
      tokenStorage.set(data);
      flushQueue(data.access_token);

      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      originalRequest._retried = true;
      return apiClient(originalRequest);
    } catch (refreshError) {
      flushQueue(null, refreshError);
      onAuthFailure();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

// ----- Error normalization ---------------------------------------------------

export interface NormalizedApiError {
  message: string;
  status: number | undefined;
  detail: unknown;
}

export function normalizeApiError(error: unknown): NormalizedApiError {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown })?.detail;
    let message: string;
    if (typeof detail === "string") {
      message = detail;
    } else if (detail && typeof detail === "object" && "message" in detail) {
      message = String((detail as { message: unknown }).message);
    } else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as {
        loc?: unknown[];
        msg?: unknown;
        type?: unknown;
      };
      const field =
        Array.isArray(first.loc) && first.loc.length > 0
          ? String(first.loc[first.loc.length - 1]).replaceAll("_", " ")
          : "This field";
      const msg =
        typeof first.msg === "string"
          ? first.msg.replace(/^Value error,\s*/i, "")
          : "Please check this value.";
      message = `${field.charAt(0).toUpperCase()}${field.slice(1)}: ${msg}`;
    } else {
      message = error.message;
    }
    return {
      message,
      status: error.response?.status,
      detail,
    };
  }
  if (error instanceof Error) {
    return { message: error.message, status: undefined, detail: undefined };
  }
  return { message: "Unknown error", status: undefined, detail: undefined };
}
