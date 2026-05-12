import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { shareApi, type ReportShareCreatePayload } from "@/api";
import { queryKeys } from "@/lib/queryKeys";

export function useReportShares(reportId: string | null) {
  return useQuery({
    queryKey: queryKeys.reports.shares(reportId ?? ""),
    queryFn: () => shareApi.list(reportId!),
    enabled: !!reportId,
  });
}

export function useCreateReportShare(reportId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: ReportShareCreatePayload) =>
      shareApi.create(reportId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.reports.shares(reportId) });
    },
  });
}

export function useRevokeReportShare(reportId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (shareId: string) => shareApi.revoke(shareId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.reports.shares(reportId) });
    },
  });
}

export function usePublicReport(token: string | null) {
  return useQuery({
    queryKey: queryKeys.publicReports.detail(token ?? ""),
    queryFn: () => shareApi.fetchPublic(token!),
    enabled: !!token,
    retry: false,
  });
}
