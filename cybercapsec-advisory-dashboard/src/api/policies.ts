import { apiClient } from "@/api/client";
import type {
  Policy,
  PolicyAcknowledgment,
  PolicySummary,
  PolicyTemplate,
  PolicyTemplateCode,
} from "@/types/api";

export const policyApi = {
  listTemplates: async (): Promise<PolicyTemplate[]> => {
    const { data } = await apiClient.get<PolicyTemplate[]>(
      "/policy-templates",
    );
    return data;
  },

  getTemplate: async (code: string): Promise<PolicyTemplate> => {
    const { data } = await apiClient.get<PolicyTemplate>(
      `/policy-templates/${code}`,
    );
    return data;
  },

  list: async (): Promise<PolicySummary[]> => {
    const { data } = await apiClient.get<PolicySummary[]>("/policies");
    return data;
  },

  get: async (id: string): Promise<Policy> => {
    const { data } = await apiClient.get<Policy>(`/policies/${id}`);
    return data;
  },

  create: async (
    template_code: PolicyTemplateCode,
    variable_overrides?: Record<string, unknown>,
  ): Promise<Policy> => {
    const { data } = await apiClient.post<Policy>("/policies", {
      template_code,
      variable_overrides,
    });
    return data;
  },

  starterPack: async (): Promise<{ generated: PolicySummary[] }> => {
    const { data } = await apiClient.post<{ generated: PolicySummary[] }>(
      "/policies/starter-pack",
    );
    return data;
  },

  publish: async (id: string): Promise<Policy> => {
    const { data } = await apiClient.post<Policy>(`/policies/${id}/publish`);
    return data;
  },

  archive: async (id: string): Promise<Policy> => {
    const { data } = await apiClient.post<Policy>(`/policies/${id}/archive`);
    return data;
  },

  acknowledge: async (
    id: string,
    acknowledgedText?: string,
  ): Promise<PolicyAcknowledgment> => {
    const { data } = await apiClient.post<PolicyAcknowledgment>(
      `/policies/${id}/acknowledge`,
      { acknowledged_text: acknowledgedText ?? null },
    );
    return data;
  },

  acknowledgments: async (id: string): Promise<PolicyAcknowledgment[]> => {
    const { data } = await apiClient.get<PolicyAcknowledgment[]>(
      `/policies/${id}/acknowledgments`,
    );
    return data;
  },
};
