import { Suspense, lazy, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/AppLayout";
import { RequireAuth, RequireGuest, RequirePaidLicense } from "@/routes/Guards";

const AssessmentPage = lazy(() =>
  import("@/pages/AssessmentPage").then((module) => ({
    default: module.AssessmentPage,
  })),
);
const BillingPage = lazy(() =>
  import("@/pages/BillingPage").then((module) => ({
    default: module.BillingPage,
  })),
);
const DashboardPage = lazy(() =>
  import("@/pages/DashboardPage").then((module) => ({
    default: module.DashboardPage,
  })),
);
const EvidencePage = lazy(() =>
  import("@/pages/EvidencePage").then((module) => ({
    default: module.EvidencePage,
  })),
);
const FrameworksPage = lazy(() =>
  import("@/pages/FrameworksPage").then((module) => ({
    default: module.FrameworksPage,
  })),
);
const LearnPage = lazy(() =>
  import("@/pages/LearnPage").then((module) => ({
    default: module.LearnPage,
  })),
);
const LoginPage = lazy(() =>
  import("@/pages/LoginPage").then((module) => ({
    default: module.LoginPage,
  })),
);
const OnboardingPage = lazy(() =>
  import("@/pages/OnboardingPage").then((module) => ({
    default: module.OnboardingPage,
  })),
);
const PoliciesPage = lazy(() =>
  import("@/pages/PoliciesPage").then((module) => ({
    default: module.PoliciesPage,
  })),
);
const PolicyDetailPage = lazy(() =>
  import("@/pages/PolicyDetailPage").then((module) => ({
    default: module.PolicyDetailPage,
  })),
);
const PublicReportPage = lazy(() =>
  import("@/pages/PublicReportPage").then((module) => ({
    default: module.PublicReportPage,
  })),
);
const QuickBaselinePage = lazy(() =>
  import("@/pages/QuickBaselinePage").then((module) => ({
    default: module.QuickBaselinePage,
  })),
);
const QuestionnairePage = lazy(() =>
  import("@/pages/QuestionnairePage").then((module) => ({
    default: module.QuestionnairePage,
  })),
);
const ReportsListPage = lazy(() =>
  import("@/pages/ReportPages").then((module) => ({
    default: module.ReportsListPage,
  })),
);
const ReportDetailPage = lazy(() =>
  import("@/pages/ReportPages").then((module) => ({
    default: module.ReportDetailPage,
  })),
);
const RoadmapPage = lazy(() =>
  import("@/pages/RoadmapPage").then((module) => ({
    default: module.RoadmapPage,
  })),
);
const SignupPage = lazy(() =>
  import("@/pages/SignupPage").then((module) => ({
    default: module.SignupPage,
  })),
);
const TeamPage = lazy(() =>
  import("@/pages/TeamPage").then((module) => ({
    default: module.TeamPage,
  })),
);

function RouteFallback() {
  return (
    <div className="flex items-center justify-center py-24">
      <div
        role="status"
        aria-label="Loading page"
        className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent"
      />
    </div>
  );
}

function LazyRoute({ children }: { children: ReactNode }) {
  return <Suspense fallback={<RouteFallback />}>{children}</Suspense>;
}

function ProtectedRoute({
  children,
  requiresLicense = true,
}: {
  children: ReactNode;
  requiresLicense?: boolean;
}) {
  return (
    <RequireAuth>
      <AppLayout>
        <LazyRoute>
          {requiresLicense ? (
            <RequirePaidLicense>{children}</RequirePaidLicense>
          ) : (
            children
          )}
        </LazyRoute>
      </AppLayout>
    </RequireAuth>
  );
}

function GuestRoute({ children }: { children: ReactNode }) {
  return (
    <RequireGuest>
      <LazyRoute>{children}</LazyRoute>
    </RequireGuest>
  );
}

export function App() {
  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={
          <GuestRoute>
            <LoginPage />
          </GuestRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <GuestRoute>
            <SignupPage />
          </GuestRoute>
        }
      />

      {/* Authenticated app */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assessment"
        element={
          <ProtectedRoute>
            <AssessmentPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/frameworks"
        element={
          <ProtectedRoute>
            <FrameworksPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/quick-baseline"
        element={
          <ProtectedRoute>
            <QuickBaselinePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/questionnaire"
        element={
          <ProtectedRoute>
            <QuestionnairePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/learn"
        element={
          <ProtectedRoute>
            <LearnPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/roadmap"
        element={
          <ProtectedRoute>
            <RoadmapPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/policies"
        element={
          <ProtectedRoute>
            <PoliciesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/policies/:policyId"
        element={
          <ProtectedRoute>
            <PolicyDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/evidence"
        element={
          <ProtectedRoute>
            <EvidencePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports/:reportId"
        element={
          <ProtectedRoute>
            <ReportDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/billing"
        element={
          <ProtectedRoute requiresLicense={false}>
            <BillingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/billing/return"
        element={
          <ProtectedRoute requiresLicense={false}>
            <BillingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/team"
        element={
          <ProtectedRoute>
            <TeamPage />
          </ProtectedRoute>
        }
      />

      {/* Public shared report */}
      <Route
        path="/shared/reports/:token"
        element={
          <LazyRoute>
            <PublicReportPage />
          </LazyRoute>
        }
      />

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
