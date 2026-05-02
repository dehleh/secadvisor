import { apiClient } from "@/api/client";
import type {
  RoadmapItem,
  RoadmapProgress,
  RoadmapStatus,
} from "@/types/api";

export interface RoadmapItemUpdatePayload {
  status?: RoadmapStatus;
  assignee_user_id?: string | null;
  due_date?: string | null;
  notes?: string | null;
  blocked_reason?: string | null;
}

export const roadmapApi = {
  list: async (params: {
    report_id?: string;
    status_filter?: RoadmapStatus;
  } = {}): Promise<RoadmapItem[]> => {
    const { data } = await apiClient.get<RoadmapItem[]>("/roadmap/items", {
      params,
    });
    return data;
  },

  get: async (id: string): Promise<RoadmapItem> => {
    const { data } = await apiClient.get<RoadmapItem>(`/roadmap/items/${id}`);
    return data;
  },

  update: async (
    id: string,
    payload: RoadmapItemUpdatePayload,
  ): Promise<RoadmapItem> => {
    const { data } = await apiClient.patch<RoadmapItem>(
      `/roadmap/items/${id}`,
      payload,
    );
    return data;
  },

  seedFromReport: async (
    reportId: string,
  ): Promise<{ seeded: number; items: RoadmapItem[] }> => {
    const { data } = await apiClient.post<{
      seeded: number;
      items: RoadmapItem[];
    }>(`/roadmap/seed-from-report/${reportId}`);
    return data;
  },

  progress: async (report_id?: string): Promise<RoadmapProgress> => {
    const { data } = await apiClient.get<RoadmapProgress>(
      "/roadmap/progress",
      { params: { report_id } },
    );
    return data;
  },
};
