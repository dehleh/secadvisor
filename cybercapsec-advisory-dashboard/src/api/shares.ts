import { apiClient } from "@/api/client";
import type { PublicReport, ReportShare } from "@/types/api";

export interface ReportShareCreatePayload {
  label?: string;
  expires_in_days?: number;
}

export const shareApi = {
  list: async (reportId: string): Promise<ReportShare[]> => {
    const { data } = await apiClient.get<ReportShare[]>(
      `/reports/${reportId}/shares`,
    );
    return data;
  },

  create: async (
    reportId: string,
    payload: ReportShareCreatePayload,
  ): Promise<ReportShare> => {
    const { data } = await apiClient.post<ReportShare>(
      `/reports/${reportId}/shares`,
      payload,
    );
    return data;
  },

  revoke: async (shareId: string): Promise<void> => {
    await apiClient.delete(`/reports/shares/${shareId}`);
  },

  fetchPublic: async (token: string): Promise<PublicReport> => {
    const { data } = await apiClient.get<PublicReport>(
      `/public/reports/${token}`,
    );
    return data;
  },
};
