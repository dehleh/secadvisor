import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { guidedReadinessApi } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { GuidedReadinessPayload } from "@/types/api";

export function useGuidedReadiness() {
  return useQuery({
    queryKey: queryKeys.guidedReadiness.profile,
    queryFn: () => guidedReadinessApi.get(),
  });
}

export function useSaveGuidedReadiness() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: GuidedReadinessPayload) =>
      guidedReadinessApi.save(payload),
    onSuccess: (data) => {
      qc.setQueryData(queryKeys.guidedReadiness.profile, data);
    },
  });
}

export function useClearGuidedReadiness() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => guidedReadinessApi.clear(),
    onSuccess: () => {
      qc.setQueryData(queryKeys.guidedReadiness.profile, null);
    },
  });
}
