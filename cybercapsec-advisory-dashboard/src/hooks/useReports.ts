import { useQuery } from "@tanstack/react-query";

import { reportApi } from "@/api";
import { queryKeys } from "@/lib/queryKeys";

export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports.all,
    queryFn: () => reportApi.list(),
  });
}

export function useReport(id: string | null) {
  return useQuery({
    queryKey: queryKeys.reports.detail(id ?? ""),
    queryFn: () => reportApi.get(id!),
    enabled: !!id,
  });
}

export function useReportsForAssessment(assessmentId: string | null) {
  return useQuery({
    queryKey: queryKeys.reports.byAssessment(assessmentId ?? ""),
    queryFn: () => reportApi.byAssessment(assessmentId!),
    enabled: !!assessmentId,
  });
}
