// Centralized query key factory. Every TanStack Query call uses these
// to ensure consistent invalidation. The hierarchy mirrors the API:
//
//   ["assessments"]                     -> all assessments
//   ["assessments", id]                 -> single assessment
//   ["assessments", id, "progress"]     -> progress sub-resource
//
// Invalidating ["assessments"] also invalidates everything beneath it.

export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },

  questionnaire: {
    all: ["questionnaire"] as const,
    version: (v: string) => ["questionnaire", v] as const,
  },

  assessments: {
    all: ["assessments"] as const,
    detail: (id: string) => ["assessments", id] as const,
    progress: (id: string) => ["assessments", id, "progress"] as const,
  },

  reports: {
    all: ["reports"] as const,
    detail: (id: string) => ["reports", id] as const,
    byAssessment: (assessmentId: string) =>
      ["reports", "by-assessment", assessmentId] as const,
    shares: (id: string) => ["reports", id, "shares"] as const,
  },

  policies: {
    all: ["policies"] as const,
    detail: (id: string) => ["policies", id] as const,
    acknowledgments: (id: string) =>
      ["policies", id, "acknowledgments"] as const,
    templates: ["policy-templates"] as const,
    template: (code: string) => ["policy-templates", code] as const,
  },

  evidence: {
    all: ["evidence"] as const,
    detail: (id: string) => ["evidence", id] as const,
    byControl: (fw: string, code: string) =>
      ["evidence", "by-control", fw, code] as const,
    coverage: ["evidence", "coverage"] as const,
  },

  guidedReadiness: {
    profile: ["guided-readiness"] as const,
  },

  roadmap: {
    items: (params: Record<string, string | undefined> = {}) =>
      ["roadmap", "items", params] as const,
    detail: (id: string) => ["roadmap", "items", id] as const,
    progress: (reportId?: string) =>
      ["roadmap", "progress", reportId ?? "all"] as const,
  },

  billing: {
    pricing: ["billing", "pricing"] as const,
    subscription: ["billing", "subscription"] as const,
  },

  users: {
    all: ["users"] as const,
  },

  publicReports: {
    detail: (token: string) => ["public-reports", token] as const,
  },
} as const;
