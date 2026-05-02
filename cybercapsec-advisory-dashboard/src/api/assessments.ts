import { apiClient } from "@/api/client";
import type {
  Assessment,
  AssessmentProgress,
  AssessmentSubmitResponse,
  Questionnaire,
} from "@/types/api";

export const assessmentApi = {
  getQuestionnaire: async (
    version: string = "latest",
  ): Promise<Questionnaire> => {
    const { data } = await apiClient.get<Questionnaire>(
      `/questionnaires/${version}`,
    );
    return data;
  },

  list: async (): Promise<Assessment[]> => {
    const { data } = await apiClient.get<Assessment[]>("/assessments");
    return data;
  },

  get: async (id: string): Promise<Assessment> => {
    const { data } = await apiClient.get<Assessment>(`/assessments/${id}`);
    return data;
  },

  create: async (
    questionnaire_version?: string,
  ): Promise<Assessment> => {
    const { data } = await apiClient.post<Assessment>("/assessments", {
      questionnaire_version,
    });
    return data;
  },

  saveResponses: async (
    id: string,
    responses: Record<string, unknown>,
    merge: boolean = true,
  ): Promise<Assessment> => {
    const { data } = await apiClient.patch<Assessment>(
      `/assessments/${id}/responses`,
      { responses, merge },
    );
    return data;
  },

  progress: async (id: string): Promise<AssessmentProgress> => {
    const { data } = await apiClient.get<AssessmentProgress>(
      `/assessments/${id}/progress`,
    );
    return data;
  },

  submit: async (id: string): Promise<AssessmentSubmitResponse> => {
    const { data } = await apiClient.post<AssessmentSubmitResponse>(
      `/assessments/${id}/submit`,
    );
    return data;
  },
};
