import { apiClient } from "@/api/client";
import type {
  GuidedReadinessPayload,
  GuidedReadinessProfile,
} from "@/types/api";

export const guidedReadinessApi = {
  async get(): Promise<GuidedReadinessProfile | null> {
    const { data } =
      await apiClient.get<GuidedReadinessProfile | null>("/guided-readiness");
    return data;
  },

  async save(payload: GuidedReadinessPayload): Promise<GuidedReadinessProfile> {
    const { data } = await apiClient.put<GuidedReadinessProfile>(
      "/guided-readiness",
      payload,
    );
    return data;
  },

  async clear(): Promise<void> {
    await apiClient.delete("/guided-readiness");
  },
};
