import { apiClient } from "@/api/client";
import type { TeamUser, UserInviteResponse, UserRole } from "@/types/api";

export interface UserInvitePayload {
  email: string;
  full_name: string;
  job_title?: string;
  role: UserRole;
}

export interface UserUpdatePayload {
  full_name?: string;
  job_title?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
}

export const userApi = {
  list: async (): Promise<TeamUser[]> => {
    const { data } = await apiClient.get<TeamUser[]>("/users");
    return data;
  },

  invite: async (payload: UserInvitePayload): Promise<UserInviteResponse> => {
    const { data } = await apiClient.post<UserInviteResponse>(
      "/users",
      payload,
    );
    return data;
  },

  update: async (id: string, payload: UserUpdatePayload): Promise<TeamUser> => {
    const { data } = await apiClient.patch<TeamUser>(`/users/${id}`, payload);
    return data;
  },

  changeMyPassword: async (payload: PasswordChangePayload): Promise<void> => {
    await apiClient.post("/users/me/password", payload);
  },
};
