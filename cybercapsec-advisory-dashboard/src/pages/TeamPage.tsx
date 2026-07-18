import { useEffect, useState } from "react";
import { Copy, KeyRound, ListChecks, ShieldCheck, UserPlus, X } from "lucide-react";

import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageHeader";
import {
  Badge,
  Card,
  CardBody,
  EmptyState,
  ErrorMessage,
  LoadingPage,
  Spinner,
} from "@/components/UI";
import { normalizeApiError } from "@/api";
import { useAuth } from "@/context/AuthContext";
import {
  useChangeMyPassword,
  useInviteUser,
  useTeamUsers,
  useUpdateUser,
} from "@/hooks/useUsers";
import type { TeamUser, UserRole } from "@/types/api";

const ROLE_OPTIONS: Array<{ value: UserRole; label: string; hint: string }> = [
  { value: "owner", label: "Owner", hint: "Full access including billing" },
  { value: "admin", label: "Admin", hint: "Full access except billing" },
  { value: "member", label: "Member", hint: "Standard read/write" },
  {
    value: "auditor",
    label: "Auditor",
    hint: "Read-only access to evidence and reports",
  },
];

const ROLE_LABEL: Record<UserRole, string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
  auditor: "Auditor",
};

const ROLE_VARIANT: Record<UserRole, "brand" | "info" | "neutral"> = {
  owner: "brand",
  admin: "info",
  member: "neutral",
  auditor: "neutral",
};

export function TeamPage() {
  const { user } = useAuth();
  const { data: users, isLoading, error } = useTeamUsers();
  const [showInvite, setShowInvite] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const isAdmin = user?.role === "owner" || user?.role === "admin";

  if (isLoading) return <LoadingPage />;
  if (error)
    return <ErrorMessage message={normalizeApiError(error).message} />;

  return (
    <>
      <PageHeader
        title="Team"
        description="Bring the right people into your cybersecurity program and assign ownership for evidence, policies, roadmap tasks, and reviews."
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPassword(true)}
            >
              <KeyRound className="h-4 w-4" /> Change password
            </Button>
            {isAdmin && (
              <Button size="sm" onClick={() => setShowInvite(true)}>
                <UserPlus className="h-4 w-4" /> Invite user
              </Button>
            )}
          </div>
        }
      />

      <Card className="mb-6 border-brand-200 bg-brand-50/40">
        <CardBody className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="flex gap-3">
            <ShieldCheck className="mt-1 h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                Security champion
              </div>
              <p className="mt-1 text-sm text-slate-600">
                Invite a CTO, security lead, or operations owner to drive fixes.
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <ListChecks className="mt-1 h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                Task owners
              </div>
              <p className="mt-1 text-sm text-slate-600">
                Add teammates who can complete roadmap work and provide evidence.
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <UserPlus className="mt-1 h-5 w-5 text-brand-700" />
            <div>
              <div className="text-sm font-semibold text-slate-900">
                Reviewers
              </div>
              <p className="mt-1 text-sm text-slate-600">
                Use auditor access for read-only due diligence or advisory reviews.
              </p>
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        {!users || users.length === 0 ? (
          <CardBody>
            <EmptyState
              title="No team members yet"
              description="Invite a teammate to collaborate."
            />
          </CardBody>
        ) : (
          <CardBody className="-mx-5 -my-4 divide-y divide-slate-100">
            {users.map((u) => (
              <UserRow key={u.id} u={u} canEdit={isAdmin} />
            ))}
          </CardBody>
        )}
      </Card>

      {showInvite && <InviteModal onClose={() => setShowInvite(false)} />}
      {showPassword && (
        <PasswordModal onClose={() => setShowPassword(false)} />
      )}
    </>
  );
}

// ----- Row -------------------------------------------------------------------

function UserRow({ u, canEdit }: { u: TeamUser; canEdit: boolean }) {
  const { user: me } = useAuth();
  const update = useUpdateUser();
  const isMe = me?.id === u.id;
  const isOwnerActor = me?.role === "owner";

  const handleRole = (role: UserRole) => {
    update.mutate({ id: u.id, payload: { role } });
  };
  const handleToggle = () => {
    update.mutate({ id: u.id, payload: { is_active: !u.is_active } });
  };

  return (
    <div className="px-5 py-4 flex items-center justify-between gap-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <div className="font-medium text-slate-900">{u.full_name}</div>
          {isMe && <Badge variant="info">You</Badge>}
          {!u.is_active && <Badge variant="danger">Disabled</Badge>}
        </div>
        <div className="text-sm text-slate-500 truncate">{u.email}</div>
        {u.job_title && (
          <div className="text-xs text-slate-500 mt-0.5">{u.job_title}</div>
        )}
      </div>
      <div className="flex items-center gap-3 shrink-0">
        {canEdit && isOwnerActor && !isMe ? (
          <select
            value={u.role}
            onChange={(e) => handleRole(e.target.value as UserRole)}
            className="rounded-md border border-slate-300 px-2 py-1 text-xs"
          >
            {ROLE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        ) : (
          <Badge variant={ROLE_VARIANT[u.role]}>{ROLE_LABEL[u.role]}</Badge>
        )}
        {canEdit && !isMe && (
          <Button variant="ghost" size="sm" onClick={handleToggle}>
            {u.is_active ? "Disable" : "Re-enable"}
          </Button>
        )}
      </div>
    </div>
  );
}

// ----- Invite modal ---------------------------------------------------------

function InviteModal({ onClose }: { onClose: () => void }) {
  const invite = useInviteUser();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [role, setRole] = useState<UserRole>("member");
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await invite.mutateAsync({
      email,
      full_name: fullName,
      job_title: jobTitle || undefined,
      role,
    });
    setTempPassword(res.temporary_password);
  };

  const copyPassword = async () => {
    if (!tempPassword) return;
    await navigator.clipboard.writeText(tempPassword);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Invite user
            </h2>
            <p className="mt-0.5 text-sm text-slate-600">
              Add someone to own security work, upload evidence, review policies,
              or inspect reports.
            </p>
          </div>
          <button onClick={onClose} aria-label="Close">
            <X className="h-5 w-5 text-slate-500" />
          </button>
        </div>
        {tempPassword ? (
          <div className="px-6 py-5 space-y-4">
            <div className="text-sm text-slate-700">
              <strong>{fullName}</strong> has been invited.
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3 text-sm text-amber-900">
              <p className="font-semibold mb-1">Share this temporary password</p>
              <p className="text-xs mb-2">
                Send it via your usual secure channel (Slack, WhatsApp, etc.).
                We don't have email yet, so this is a one-time copy.
              </p>
              <div className="flex items-center gap-2 bg-white rounded border border-amber-200 px-3 py-2 font-mono text-sm">
                <span className="flex-1 truncate">{tempPassword}</span>
                <button
                  onClick={copyPassword}
                  className="text-brand-700 hover:text-brand-800"
                >
                  {copied ? (
                    <span className="text-xs font-medium">Copied</span>
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
            <Button onClick={onClose} className="w-full">
              Done
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5 space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Full name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Job title (optional)
              </label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                {ROLE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label} — {o.hint}
                  </option>
                ))}
              </select>
            </div>
            {invite.error && (
              <ErrorMessage
                message={normalizeApiError(invite.error).message}
              />
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={invite.isPending}>
                {invite.isPending ? <Spinner className="h-4 w-4" /> : null}
                Send invite
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ----- Password modal --------------------------------------------------------

function PasswordModal({ onClose }: { onClose: () => void }) {
  const change = useChangeMyPassword();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [done, setDone] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!done) return;
    const t = setTimeout(onClose, 1500);
    return () => clearTimeout(t);
  }, [done, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    if (next.length < 8) {
      setLocalError("New password must be at least 8 characters.");
      return;
    }
    if (next !== confirm) {
      setLocalError("Passwords do not match.");
      return;
    }
    await change.mutateAsync({ current_password: current, new_password: next });
    setDone(true);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900">
            Change password
          </h2>
          <button onClick={onClose} aria-label="Close">
            <X className="h-5 w-5 text-slate-500" />
          </button>
        </div>
        {done ? (
          <div className="px-6 py-8 text-center">
            <div className="text-sm font-medium text-emerald-700">
              Password updated.
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5 space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Current password
              </label>
              <input
                type="password"
                required
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                New password
              </label>
              <input
                type="password"
                required
                value={next}
                onChange={(e) => setNext(e.target.value)}
                minLength={8}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">
                Confirm new password
              </label>
              <input
                type="password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                minLength={8}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            {(localError || change.error) && (
              <ErrorMessage
                message={
                  localError ??
                  normalizeApiError(change.error).message
                }
              />
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={change.isPending}>
                {change.isPending ? <Spinner className="h-4 w-4" /> : null}
                Update
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
