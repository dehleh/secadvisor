import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  BookOpen,
  ClipboardCheck,
  CreditCard,
  FileText,
  GraduationCap,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Menu,
  MessageSquareText,
  ShieldCheck,
  FilePlus2,
  Target,
  Zap,
  Users,
  X,
} from "lucide-react";

import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";
import { cn } from "@/lib/cn";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/onboarding", label: "Program setup", icon: Target },
  { to: "/frameworks", label: "Guides", icon: BookOpen },
  { to: "/quick-baseline", label: "Quick baseline", icon: Zap },
  { to: "/questionnaire", label: "Questionnaire", icon: MessageSquareText },
  { to: "/learn", label: "Learn", icon: GraduationCap },
  { to: "/assessment", label: "Assessment", icon: ClipboardCheck },
  { to: "/roadmap", label: "Roadmap", icon: ListChecks },
  { to: "/policies", label: "Policies", icon: FileText },
  { to: "/evidence", label: "Evidence", icon: FilePlus2 },
  { to: "/reports", label: "Reports", icon: ShieldCheck },
  { to: "/team", label: "Team", icon: Users },
  { to: "/billing", label: "Billing", icon: CreditCard },
] as const;

function NavigationLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <>
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-700 hover:bg-slate-100",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        );
      })}
    </>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50 lg:flex">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white lg:hidden">
        <div className="flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="CyberCapSec" className="h-8 w-8" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                CyberCapSec
              </div>
              <div className="text-xs text-slate-500">Security program</div>
            </div>
          </div>
          <button
            type="button"
            className="rounded-md p-2 text-slate-700 hover:bg-slate-100"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? "Close navigation" : "Open navigation"}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {mobileOpen && (
          <div className="border-t border-slate-200 px-3 py-3">
            <nav className="space-y-1">
              <NavigationLinks onNavigate={() => setMobileOpen(false)} />
            </nav>
            <Button
              variant="ghost"
              size="sm"
              className="mt-3 w-full justify-start"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </Button>
          </div>
        )}
      </header>

      {/* Sidebar */}
      <aside className="hidden w-64 bg-white border-r border-slate-200 lg:flex flex-col">
        <div className="px-5 py-5 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="CyberCapSec" className="h-9 w-9" />
            <div>
              <div className="font-semibold text-slate-900 text-sm">
                CyberCapSec
              </div>
              <div className="text-xs text-slate-500">Advisory</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavigationLinks />
        </nav>

        <div className="px-3 py-3 border-t border-slate-200">
          <div className="px-3 py-2">
            <div className="text-sm font-medium text-slate-900 truncate">
              {user?.full_name}
            </div>
            <div className="text-xs text-slate-500 truncate">{user?.email}</div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
