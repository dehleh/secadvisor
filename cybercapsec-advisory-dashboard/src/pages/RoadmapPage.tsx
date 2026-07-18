import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Calendar } from "lucide-react";

import { Button } from "@/components/Button";
import { Textarea } from "@/components/Field";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  CardHeader,
  CardTitle,
  EmptyState,
  ErrorMessage,
  LoadingPage,
  SeverityBadge,
  StatusBadge,
} from "@/components/UI";
import { useRoadmapItems, useRoadmapProgress, useUpdateRoadmapItem } from "@/hooks/useRoadmap";
import { normalizeApiError } from "@/api";
import type { RoadmapItem, RoadmapStatus } from "@/types/api";
import { cn } from "@/lib/cn";

const COLUMNS: Array<{ status: RoadmapStatus; title: string }> = [
  { status: "todo", title: "To do" },
  { status: "in_progress", title: "In progress" },
  { status: "blocked", title: "Blocked" },
  { status: "done", title: "Done" },
];

function ItemCard({
  item,
  onClick,
}: {
  item: RoadmapItem;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white border border-slate-200 rounded-md p-3 hover:border-brand-400 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <SeverityBadge severity={item.severity} />
        <span className="text-xs text-slate-500">W{item.week_target}</span>
      </div>
      <div className="text-sm font-medium text-slate-900 mb-1.5">
        {item.title}
      </div>
      {item.framework_citations.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1">
          {item.framework_citations.slice(0, 2).map((c, i) => (
            <Badge key={i} variant="neutral">
              {c.framework} {c.control_code}
            </Badge>
          ))}
          {item.framework_citations.length > 2 && (
            <Badge variant="neutral">
              +{item.framework_citations.length - 2}
            </Badge>
          )}
        </div>
      )}
      <Badge variant="neutral">{item.effort.replace("_", " ")}</Badge>
    </button>
  );
}

function ItemDetail({
  item,
  onClose,
}: {
  item: RoadmapItem;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const update = useUpdateRoadmapItem();
  const [notes, setNotes] = useState(item.notes ?? "");
  const [blockedReason, setBlockedReason] = useState(item.blocked_reason ?? "");
  const [error, setError] = useState<string | null>(null);

  const setStatus = async (status: RoadmapStatus) => {
    setError(null);
    try {
      await update.mutateAsync({
        id: item.id,
        payload: {
          status,
          ...(status === "blocked" && blockedReason
            ? { blocked_reason: blockedReason }
            : {}),
        },
      });
    } catch (err) {
      setError(normalizeApiError(err).message);
    }
  };

  const saveNotes = async () => {
    setError(null);
    try {
      await update.mutateAsync({
        id: item.id,
        payload: { notes },
      });
    } catch (err) {
      setError(normalizeApiError(err).message);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
        <CardHeader className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <SeverityBadge severity={item.severity} />
              <StatusBadge status={item.status} />
              <Badge variant="neutral">Week {item.week_target}</Badge>
              <Badge variant="neutral">{item.effort.replace("_", " ")}</Badge>
            </div>
            <CardTitle>{item.title}</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close
          </Button>
        </CardHeader>
        <CardBody className="space-y-5">
          {error && <ErrorMessage message={error} />}

          <section>
            <h3 className="text-sm font-semibold text-slate-900 mb-1">
              Description
            </h3>
            <p className="text-sm text-slate-700 whitespace-pre-wrap">
              {item.description}
            </p>
          </section>

          {item.success_criteria.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-slate-900 mb-2">
                Success criteria
              </h3>
              <ul className="space-y-1">
                {item.success_criteria.map((c, i) => (
                  <li
                    key={i}
                    className="text-sm text-slate-700 flex gap-2"
                  >
                    <span className="text-emerald-600 flex-shrink-0">✓</span>
                    {c}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {item.framework_citations.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-slate-900 mb-2">
                Framework citations
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {item.framework_citations.map((c, i) => (
                  <Badge key={i} variant="brand">
                    {c.framework} {c.control_code}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          <section className="rounded-md border border-brand-200 bg-brand-50 p-3">
            <h3 className="text-sm font-semibold text-slate-900 mb-1">
              Evidence handoff
            </h3>
            <p className="text-sm text-slate-700">
              When this work is started or completed, attach evidence so the
              control is useful for security reviews, customer due diligence,
              and compliance mapping.
            </p>
            <Button
              className="mt-3"
              size="sm"
              variant="outline"
              onClick={() => navigate("/evidence")}
            >
              Add evidence for this work
            </Button>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-slate-900 mb-2">
              Status
            </h3>
            <div className="flex flex-wrap gap-2">
              {(["todo", "in_progress", "blocked", "done"] as RoadmapStatus[]).map(
                (s) => (
                  <Button
                    key={s}
                    size="sm"
                    variant={item.status === s ? "primary" : "outline"}
                    onClick={() => void setStatus(s)}
                    disabled={update.isPending}
                  >
                    <StatusBadge status={s} />
                  </Button>
                ),
              )}
            </div>
            {item.status === "blocked" && (
              <Textarea
                className="mt-3"
                label="Blocked reason"
                value={blockedReason}
                onChange={(e) => setBlockedReason(e.target.value)}
                onBlur={() =>
                  blockedReason !== item.blocked_reason &&
                  update.mutate({
                    id: item.id,
                    payload: { blocked_reason: blockedReason },
                  })
                }
              />
            )}
          </section>

          <section>
            <Textarea
              label="Notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              hint="Internal notes. Auto-saved on blur."
              onBlur={() => notes !== item.notes && void saveNotes()}
            />
          </section>

          {item.completed_at && (
            <p className="text-sm text-emerald-700">
              ✓ Completed{" "}
              {new Date(item.completed_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </p>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

export function RoadmapPage() {
  const { data: items, isLoading, error } = useRoadmapItems();
  const { data: progress } = useRoadmapProgress();
  const [selected, setSelected] = useState<RoadmapItem | null>(null);

  const grouped = useMemo(() => {
    const map: Record<RoadmapStatus, RoadmapItem[]> = {
      todo: [],
      in_progress: [],
      blocked: [],
      done: [],
      cancelled: [],
    };
    if (items) {
      for (const item of items) map[item.status].push(item);
    }
    return map;
  }, [items]);

  if (isLoading) return <LoadingPage />;
  if (error) return <ErrorMessage message={normalizeApiError(error).message} />;

  if (!items?.length) {
    return (
      <>
        <PageHeader title="Roadmap" />
        <Card>
          <CardBody>
            <EmptyState
              icon={<Calendar className="h-12 w-12" />}
              title="No roadmap yet"
              description="Complete an assessment to generate your tailored 13-week roadmap."
            />
          </CardBody>
        </Card>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Roadmap"
        description={
          progress
            ? `${progress.completion_pct}% complete · ${progress.done} of ${progress.total} done`
            : undefined
        }
      />

      {/* Progress bar */}
      {progress && (
        <div className="mb-6">
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-500 to-brand-600 transition-all"
              style={{ width: `${progress.completion_pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Kanban columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {COLUMNS.map((col) => (
          <div key={col.status} className="min-w-0">
            <div className="flex items-center justify-between mb-3 px-1">
              <h2 className="text-sm font-semibold text-slate-900">
                {col.title}
              </h2>
              <Badge variant="neutral">
                {grouped[col.status].length}
              </Badge>
            </div>
            <div
              className={cn(
                "min-h-[200px] rounded-lg p-2 space-y-2",
                col.status === "todo" && "bg-slate-100",
                col.status === "in_progress" && "bg-sky-50",
                col.status === "blocked" && "bg-amber-50",
                col.status === "done" && "bg-emerald-50",
              )}
            >
              {grouped[col.status].length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">
                  Empty
                </p>
              ) : (
                grouped[col.status].map((item) => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onClick={() => setSelected(item)}
                  />
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {selected && (
        <ItemDetail item={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}
