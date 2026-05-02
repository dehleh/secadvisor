import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";
import type { Severity, RoadmapStatus } from "@/types/api";

// ----- Card ------------------------------------------------------------------

export function Card({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "bg-white border border-slate-200 rounded-lg shadow-sm",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("px-5 py-4 border-b border-slate-200", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-lg font-semibold text-slate-900", className)}
      {...props}
    />
  );
}

export function CardBody({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4", className)} {...props} />;
}

export function CardFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-5 py-3 border-t border-slate-200 bg-slate-50 rounded-b-lg",
        className,
      )}
      {...props}
    />
  );
}

// ----- Badge -----------------------------------------------------------------

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "neutral" | "success" | "warning" | "danger" | "info" | "brand";
}

const badgeVariantClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  neutral: "bg-slate-100 text-slate-700",
  success: "bg-emerald-100 text-emerald-800",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-sky-100 text-sky-800",
  brand: "bg-brand-100 text-brand-700",
};

export function Badge({
  variant = "neutral",
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        badgeVariantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

// ----- Severity badge --------------------------------------------------------

export function SeverityBadge({ severity }: { severity: Severity }) {
  const map: Record<Severity, BadgeProps["variant"]> = {
    critical: "danger",
    high: "danger",
    medium: "warning",
    low: "info",
    informational: "neutral",
  };
  const labelMap: Record<Severity, string> = {
    critical: "Critical",
    high: "High",
    medium: "Medium",
    low: "Low",
    informational: "Info",
  };
  return <Badge variant={map[severity]}>{labelMap[severity]}</Badge>;
}

// ----- Roadmap status badge --------------------------------------------------

export function StatusBadge({ status }: { status: RoadmapStatus }) {
  const map: Record<RoadmapStatus, BadgeProps["variant"]> = {
    todo: "neutral",
    in_progress: "info",
    blocked: "warning",
    done: "success",
    cancelled: "neutral",
  };
  const labelMap: Record<RoadmapStatus, string> = {
    todo: "To do",
    in_progress: "In progress",
    blocked: "Blocked",
    done: "Done",
    cancelled: "Cancelled",
  };
  return <Badge variant={map[status]}>{labelMap[status]}</Badge>;
}

// ----- Empty state -----------------------------------------------------------

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="text-center py-12 px-6">
      {icon && (
        <div className="mx-auto mb-4 h-12 w-12 text-slate-400">{icon}</div>
      )}
      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-slate-600 max-w-md mx-auto">
          {description}
        </p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

// ----- Loading state ---------------------------------------------------------

export function Spinner({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block h-5 w-5 animate-spin rounded-full border-2 border-brand-600 border-t-transparent",
        className,
      )}
    />
  );
}

export function LoadingPage() {
  return (
    <div className="flex items-center justify-center py-24">
      <Spinner className="h-8 w-8" />
    </div>
  );
}

// ----- Error message ---------------------------------------------------------

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">
      {message}
    </div>
  );
}

// ----- Score gauge -----------------------------------------------------------

export function ScoreRing({
  score,
  label,
  size = 120,
}: {
  score: number;
  label?: string;
  size?: number;
}) {
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const safeScore = Math.max(0, Math.min(100, score));
  const offset = circumference - (safeScore / 100) * circumference;

  let colorClass = "stroke-emerald-500";
  if (safeScore < 40) colorClass = "stroke-red-500";
  else if (safeScore < 70) colorClass = "stroke-amber-500";

  return (
    <div className="inline-flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          className="stroke-slate-200"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn("transition-all duration-500", colorClass)}
        />
      </svg>
      <div
        className="-mt-[calc(50%+1rem)] text-center"
        style={{ width: size, height: 0 }}
      >
        <div className="mt-[calc(50%-1rem)] text-2xl font-bold text-slate-900">
          {Math.round(safeScore)}
        </div>
        {label && <div className="text-xs text-slate-500">{label}</div>}
      </div>
    </div>
  );
}
