import { useEffect, useState } from "react";
import { Copy, Eye, Link2, LockKeyhole, ShieldCheck, Trash2, X } from "lucide-react";

import { Button } from "@/components/Button";
import { Badge, ErrorMessage, Spinner } from "@/components/UI";
import { normalizeApiError } from "@/api";
import {
  useCreateReportShare,
  useReportShares,
  useRevokeReportShare,
} from "@/hooks/useShares";

interface Props {
  reportId: string;
  open: boolean;
  onClose: () => void;
}

const PUBLIC_BASE =
  typeof window !== "undefined" ? window.location.origin : "";

function buildShareUrl(token: string): string {
  return `${PUBLIC_BASE}/shared/reports/${token}`;
}

function formatExpiry(expires_at: string | null): string {
  if (!expires_at) return "Never";
  const date = new Date(expires_at);
  return date.toLocaleDateString();
}

export function ShareReportModal({ reportId, open, onClose }: Props) {
  const { data: shares, isLoading, error } = useReportShares(open ? reportId : null);
  const createShare = useCreateReportShare(reportId);
  const revokeShare = useRevokeReportShare(reportId);

  const [label, setLabel] = useState("");
  const [expiresInDays, setExpiresInDays] = useState<number | "never">(30);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setLabel("");
      setExpiresInDays(30);
      setCopiedId(null);
    }
  }, [open]);

  if (!open) return null;

  const handleCreate = async () => {
    await createShare.mutateAsync({
      label: label || undefined,
      expires_in_days: expiresInDays === "never" ? undefined : expiresInDays,
    });
    setLabel("");
  };

  const handleCopy = async (token: string) => {
    const url = buildShareUrl(token);
    await navigator.clipboard.writeText(url);
    setCopiedId(token);
    setTimeout(() => setCopiedId((v) => (v === token ? null : v)), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Share this report
            </h2>
            <p className="text-sm text-slate-600 mt-0.5">
              Generate a public, read-only link for auditors, investors, or
              customers. No login required.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-slate-700"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-md border border-brand-200 bg-brand-50 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-brand-900">
                <Eye className="h-4 w-4" />
                Visible
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                Summary, risk register, roadmap, scores, framework gaps, and
                report label.
              </p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <LockKeyhole className="h-4 w-4" />
                Not visible
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                Raw assessment answers, evidence files, team notes, billing,
                users, and internal policies.
              </p>
            </div>
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
                <ShieldCheck className="h-4 w-4" />
                Controlled
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                Links can expire, be revoked, and show view count for light
                assurance.
              </p>
            </div>
          </div>

          {/* Create */}
          <div className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-900 mb-3">
              Create a new share link
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Label (optional)
                </label>
                <input
                  type="text"
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="e.g. Series A due diligence"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Expires in
                </label>
                <select
                  value={expiresInDays}
                  onChange={(e) =>
                    setExpiresInDays(
                      e.target.value === "never"
                        ? "never"
                        : Number(e.target.value),
                    )
                  }
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value={7}>7 days</option>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>1 year</option>
                </select>
              </div>
            </div>
            <div className="mt-3 flex justify-end">
              <Button
                size="sm"
                onClick={handleCreate}
                disabled={createShare.isPending}
              >
                {createShare.isPending ? (
                  <Spinner className="h-4 w-4" />
                ) : (
                  <Link2 className="h-4 w-4" />
                )}
                Generate link
              </Button>
            </div>
            {createShare.error && (
              <div className="mt-2">
                <ErrorMessage
                  message={normalizeApiError(createShare.error).message}
                />
              </div>
            )}
          </div>

          {/* Existing shares */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-2">
              Active links
            </h3>
            {isLoading && <Spinner />}
            {error && (
              <ErrorMessage message={normalizeApiError(error).message} />
            )}
            {!isLoading && (!shares || shares.length === 0) && (
              <p className="text-sm text-slate-500">
                No share links yet. Generate one above.
              </p>
            )}
            {shares && shares.length > 0 && (
              <ul className="divide-y divide-slate-100 border border-slate-200 rounded-md">
                {shares.map((s) => {
                  const url = buildShareUrl(s.token);
                  const isRevoked = !!s.revoked_at;
                  const isExpired =
                    !!s.expires_at && new Date(s.expires_at) < new Date();
                  return (
                    <li
                      key={s.id}
                      className="px-4 py-3 flex items-start justify-between gap-3"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {s.label && (
                            <span className="text-sm font-medium text-slate-900">
                              {s.label}
                            </span>
                          )}
                          {isRevoked && (
                            <Badge variant="danger">Revoked</Badge>
                          )}
                          {!isRevoked && isExpired && (
                            <Badge variant="warning">Expired</Badge>
                          )}
                          {!isRevoked && !isExpired && (
                            <Badge variant="success">Active</Badge>
                          )}
                        </div>
                        <div className="text-xs text-slate-500 truncate">
                          {url}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          Expires: {formatExpiry(s.expires_at)} · Views:{" "}
                          {s.view_count}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {!isRevoked && !isExpired && (
                          <button
                            onClick={() => handleCopy(s.token)}
                            className="p-2 text-slate-600 hover:text-brand-700"
                            title="Copy link"
                          >
                            {copiedId === s.token ? (
                              <span className="text-xs font-medium text-brand-700">
                                Copied
                              </span>
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </button>
                        )}
                        {!isRevoked && (
                          <button
                            onClick={() => revokeShare.mutate(s.id)}
                            disabled={revokeShare.isPending}
                            className="p-2 text-slate-600 hover:text-red-600"
                            title="Revoke"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
