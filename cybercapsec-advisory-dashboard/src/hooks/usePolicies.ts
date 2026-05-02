import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { policyApi } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { PolicyTemplateCode } from "@/types/api";

export function usePolicyTemplates() {
  return useQuery({
    queryKey: queryKeys.policies.templates,
    queryFn: () => policyApi.listTemplates(),
    staleTime: 1000 * 60 * 60,
  });
}

export function usePolicyTemplate(code: string | null) {
  return useQuery({
    queryKey: queryKeys.policies.template(code ?? ""),
    queryFn: () => policyApi.getTemplate(code!),
    enabled: !!code,
  });
}

export function usePolicies() {
  return useQuery({
    queryKey: queryKeys.policies.all,
    queryFn: () => policyApi.list(),
  });
}

export function usePolicy(id: string | null) {
  return useQuery({
    queryKey: queryKeys.policies.detail(id ?? ""),
    queryFn: () => policyApi.get(id!),
    enabled: !!id,
  });
}

export function usePolicyAcknowledgments(id: string | null) {
  return useQuery({
    queryKey: queryKeys.policies.acknowledgments(id ?? ""),
    queryFn: () => policyApi.acknowledgments(id!),
    enabled: !!id,
  });
}

export function useCreatePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      template_code,
      variable_overrides,
    }: {
      template_code: PolicyTemplateCode;
      variable_overrides?: Record<string, unknown>;
    }) => policyApi.create(template_code, variable_overrides),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.policies.all });
    },
  });
}

export function useStarterPack() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => policyApi.starterPack(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.policies.all });
    },
  });
}

export function usePublishPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => policyApi.publish(id),
    onSuccess: (policy) => {
      qc.invalidateQueries({ queryKey: queryKeys.policies.all });
      qc.setQueryData(queryKeys.policies.detail(policy.id), policy);
    },
  });
}

export function useArchivePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => policyApi.archive(id),
    onSuccess: (policy) => {
      qc.invalidateQueries({ queryKey: queryKeys.policies.all });
      qc.setQueryData(queryKeys.policies.detail(policy.id), policy);
    },
  });
}

export function useAcknowledgePolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      acknowledged_text,
    }: {
      id: string;
      acknowledged_text?: string;
    }) => policyApi.acknowledge(id, acknowledged_text),
    onSuccess: (_, { id }) => {
      qc.invalidateQueries({
        queryKey: queryKeys.policies.acknowledgments(id),
      });
    },
  });
}
