import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/AppLayout";
import { AssessmentPage } from "@/pages/AssessmentPage";
import { BillingPage } from "@/pages/BillingPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { EvidencePage } from "@/pages/EvidencePage";
import { LoginPage } from "@/pages/LoginPage";
import { PoliciesPage } from "@/pages/PoliciesPage";
import { PolicyDetailPage } from "@/pages/PolicyDetailPage";
import { PublicReportPage } from "@/pages/PublicReportPage";
import { ReportDetailPage, ReportsListPage } from "@/pages/ReportPages";
import { RoadmapPage } from "@/pages/RoadmapPage";
import { SignupPage } from "@/pages/SignupPage";
import { TeamPage } from "@/pages/TeamPage";
import { RequireAuth, RequireGuest } from "@/routes/Guards";

export function App() {
  return (
    <Routes>
      {/* Public */}
      <Route
        path="/login"
        element={
          <RequireGuest>
            <LoginPage />
          </RequireGuest>
        }
      />
      <Route
        path="/signup"
        element={
          <RequireGuest>
            <SignupPage />
          </RequireGuest>
        }
      />

      {/* Authenticated app */}
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <AppLayout>
              <DashboardPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/assessment"
        element={
          <RequireAuth>
            <AppLayout>
              <AssessmentPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/roadmap"
        element={
          <RequireAuth>
            <AppLayout>
              <RoadmapPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/policies"
        element={
          <RequireAuth>
            <AppLayout>
              <PoliciesPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/policies/:policyId"
        element={
          <RequireAuth>
            <AppLayout>
              <PolicyDetailPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/evidence"
        element={
          <RequireAuth>
            <AppLayout>
              <EvidencePage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/reports"
        element={
          <RequireAuth>
            <AppLayout>
              <ReportsListPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/reports/:reportId"
        element={
          <RequireAuth>
            <AppLayout>
              <ReportDetailPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/billing"
        element={
          <RequireAuth>
            <AppLayout>
              <BillingPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/billing/return"
        element={
          <RequireAuth>
            <AppLayout>
              <BillingPage />
            </AppLayout>
          </RequireAuth>
        }
      />
      <Route
        path="/team"
        element={
          <RequireAuth>
            <AppLayout>
              <TeamPage />
            </AppLayout>
          </RequireAuth>
        }
      />

      {/* Public shared report */}
      <Route path="/shared/reports/:token" element={<PublicReportPage />} />

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
