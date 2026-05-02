import { apiClient } from "@/api/client";
import type {
  AuthTokens,
  LoginPayload,
  SignupPayload,
  SignupResponse,
  User,
} from "@/types/api";

export const authApi = {
  signup: async (payload: SignupPayload): Promise<SignupResponse> => {
    const { data } = await apiClient.post<SignupResponse>(
      "/auth/signup",
      payload,
    );
    return data;
  },

  login: async (payload: LoginPayload): Promise<AuthTokens> => {
    const { data } = await apiClient.post<AuthTokens>("/auth/login", payload);
    return data;
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },
};
