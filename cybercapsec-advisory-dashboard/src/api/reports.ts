import { apiClient } from "@/api/client";
import type { Report, ReportSummary } from "@/types/api";

export const reportApi = {
  list: async (): Promise<ReportSummary[]> => {
    const { data } = await apiClient.get<ReportSummary[]>("/reports");
    return data;
  },

  get: async (id: string): Promise<Report> => {
    const { data } = await apiClient.get<Report>(`/reports/${id}`);
    return data;
  },

  byAssessment: async (assessmentId: string): Promise<ReportSummary[]> => {
    const { data } = await apiClient.get<ReportSummary[]>(
      `/reports/by-assessment/${assessmentId}`,
    );
    return data;
  },
};
