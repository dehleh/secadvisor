import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { assessmentApi } from "@/api";
import { queryKeys } from "@/lib/queryKeys";
import type { Assessment } from "@/types/api";

export function useQuestionnaire(version: string = "latest") {
  return useQuery({
    queryKey: queryKeys.questionnaire.version(version),
    queryFn: () => assessmentApi.getQuestionnaire(version),
    staleTime: 1000 * 60 * 60, // 1 hour — questionnaire rarely changes per session
  });
}

export function useAssessments() {
  return useQuery({
    queryKey: queryKeys.assessments.all,
    queryFn: () => assessmentApi.list(),
  });
}

export function useAssessment(id: string | null) {
  return useQuery({
    queryKey: queryKeys.assessments.detail(id ?? ""),
    queryFn: () => assessmentApi.get(id!),
    enabled: !!id,
  });
}

export function useAssessmentProgress(id: string | null) {
  return useQuery({
    queryKey: queryKeys.assessments.progress(id ?? ""),
    queryFn: () => assessmentApi.progress(id!),
    enabled: !!id,
  });
}

export function useCreateAssessment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (version?: string) => assessmentApi.create(version),
    onSuccess: (assessment: Assessment) => {
      qc.invalidateQueries({ queryKey: queryKeys.assessments.all });
      qc.setQueryData(queryKeys.assessments.detail(assessment.id), assessment);
    },
  });
}

export function useSaveResponses(assessmentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (responses: Record<string, unknown>) =>
      assessmentApi.saveResponses(assessmentId, responses, true),
    onSuccess: (assessment) => {
      qc.setQueryData(queryKeys.assessments.detail(assessment.id), assessment);
      qc.invalidateQueries({
        queryKey: queryKeys.assessments.progress(assessment.id),
      });
    },
  });
}

export function useSubmitAssessment(assessmentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => assessmentApi.submit(assessmentId),
    onSuccess: () => {
      // Submission generates a report and seeds the roadmap — invalidate
      // everything that could have changed.
      qc.invalidateQueries({ queryKey: queryKeys.assessments.all });
      qc.invalidateQueries({ queryKey: queryKeys.reports.all });
      qc.invalidateQueries({
        queryKey: queryKeys.assessments.detail(assessmentId),
      });
      qc.invalidateQueries({
        queryKey: ["roadmap"],
      });
    },
  });
}
