import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { roadmapApi, type RoadmapItemUpdatePayload } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { RoadmapStatus } from "@/types/api";

export function useRoadmapItems(params: {
  report_id?: string;
  status_filter?: RoadmapStatus;
} = {}) {
  return useQuery({
    queryKey: queryKeys.roadmap.items({
      report_id: params.report_id,
      status_filter: params.status_filter,
    }),
    queryFn: () => roadmapApi.list(params),
  });
}

export function useRoadmapItem(id: string | null) {
  return useQuery({
    queryKey: queryKeys.roadmap.detail(id ?? ""),
    queryFn: () => roadmapApi.get(id!),
    enabled: !!id,
  });
}

export function useRoadmapProgress(reportId?: string) {
  return useQuery({
    queryKey: queryKeys.roadmap.progress(reportId),
    queryFn: () => roadmapApi.progress(reportId),
  });
}

export function useUpdateRoadmapItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: RoadmapItemUpdatePayload;
    }) => roadmapApi.update(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roadmap"] });
    },
  });
}

export function useSeedRoadmap() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reportId: string) => roadmapApi.seedFromReport(reportId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roadmap"] });
    },
  });
}
