import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { evidenceApi, type EvidenceCreatePayload } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { EvidenceStatus } from "@/types/api";

export function useEvidenceList() {
  return useQuery({
    queryKey: queryKeys.evidence.all,
    queryFn: () => evidenceApi.list(),
  });
}

export function useEvidence(id: string | null) {
  return useQuery({
    queryKey: queryKeys.evidence.detail(id ?? ""),
    queryFn: () => evidenceApi.get(id!),
    enabled: !!id,
  });
}

export function useEvidenceForControl(framework: string, code: string) {
  return useQuery({
    queryKey: queryKeys.evidence.byControl(framework, code),
    queryFn: () => evidenceApi.byControl(framework, code),
    enabled: !!framework && !!code,
  });
}

export function useCoverageMatrix() {
  return useQuery({
    queryKey: queryKeys.evidence.coverage,
    queryFn: () => evidenceApi.coverageMatrix(),
  });
}

export function useCreateEvidence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: EvidenceCreatePayload) =>
      evidenceApi.create(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evidence"] });
    },
  });
}

export function useUpdateEvidenceStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: EvidenceStatus }) =>
      evidenceApi.updateStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evidence"] });
    },
  });
}
