import { apiClient } from "@/api/client";
import type {
  ControlEvidence,
  CoverageMatrix,
  Evidence,
  EvidenceKind,
  EvidenceStatus,
  EvidenceWithCoverage,
} from "@/types/api";

export interface EvidenceCreatePayload {
  title: string;
  description?: string | null;
  kind: EvidenceKind;
  framework_code: string;
  control_code: string;
  external_url?: string | null;
  referenced_policy_id?: string | null;
  narrative_text?: string | null;
  valid_until?: string | null;
}

export const evidenceApi = {
  list: async (): Promise<Evidence[]> => {
    const { data } = await apiClient.get<Evidence[]>("/evidence");
    return data;
  },

  get: async (id: string): Promise<EvidenceWithCoverage> => {
    const { data } = await apiClient.get<EvidenceWithCoverage>(
      `/evidence/${id}`,
    );
    return data;
  },

  create: async (
    payload: EvidenceCreatePayload,
  ): Promise<EvidenceWithCoverage> => {
    const { data } = await apiClient.post<EvidenceWithCoverage>(
      "/evidence",
      payload,
    );
    return data;
  },

  updateStatus: async (
    id: string,
    status: EvidenceStatus,
  ): Promise<Evidence> => {
    const { data } = await apiClient.patch<Evidence>(
      `/evidence/${id}/status`,
      { status },
    );
    return data;
  },

  byControl: async (
    framework_code: string,
    control_code: string,
  ): Promise<ControlEvidence> => {
    const { data } = await apiClient.get<ControlEvidence>(
      `/evidence/by-control/${framework_code}/${control_code}`,
    );
    return data;
  },

  coverageMatrix: async (): Promise<CoverageMatrix> => {
    const { data } = await apiClient.get<CoverageMatrix>(
      "/evidence/coverage/matrix",
    );
    return data;
  },
};
