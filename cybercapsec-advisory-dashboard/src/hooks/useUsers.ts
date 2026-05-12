import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  userApi,
  type PasswordChangePayload,
  type UserInvitePayload,
  type UserUpdatePayload,
} from "@/api";
import { queryKeys } from "@/lib/queryKeys";

export function useTeamUsers() {
  return useQuery({
    queryKey: queryKeys.users.all,
    queryFn: () => userApi.list(),
  });
}

export function useInviteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserInvitePayload) => userApi.invite(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UserUpdatePayload }) =>
      userApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useChangeMyPassword() {
  return useMutation({
    mutationFn: (payload: PasswordChangePayload) =>
      userApi.changeMyPassword(payload),
  });
}
