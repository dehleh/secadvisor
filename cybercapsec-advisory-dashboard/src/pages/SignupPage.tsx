import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/Button";
import { Input, Select } from "@/components/Field";
import { ErrorMessage } from "@/components/UI";
import { useAuth } from "@/context/AuthContext";
import { normalizeApiError } from "@/api";
import type { CompanySize, CompanyStage, Sector } from "@/types/api";

const SECTOR_OPTIONS: Array<{ value: Sector; label: string }> = [
  { value: "fintech", label: "Fintech" },
  { value: "healthtech", label: "Healthtech" },
  { value: "edtech", label: "Edtech" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "logistics", label: "Logistics" },
  { value: "agritech", label: "Agritech" },
  { value: "saas", label: "SaaS" },
  { value: "insurtech", label: "Insurtech" },
  { value: "proptech", label: "Proptech" },
  { value: "other", label: "Other" },
];

const SIZE_OPTIONS: Array<{ value: CompanySize; label: string }> = [
  { value: "solo", label: "Just me" },
  { value: "micro", label: "2 - 10" },
  { value: "small", label: "11 - 50" },
  { value: "medium", label: "51 - 200" },
  { value: "large", label: "201 - 1000" },
  { value: "enterprise", label: "1000+" },
];

const STAGE_OPTIONS: Array<{ value: CompanyStage; label: string }> = [
  { value: "idea", label: "Idea" },
  { value: "pre_seed", label: "Pre-seed" },
  { value: "seed", label: "Seed" },
  { value: "series_a", label: "Series A" },
  { value: "series_b", label: "Series B" },
  { value: "series_c_plus", label: "Series C+" },
  { value: "bootstrapped", label: "Bootstrapped" },
  { value: "established", label: "Established" },
];

const COUNTRY_OPTIONS = [
  { value: "NG", label: "Nigeria" },
  { value: "KE", label: "Kenya" },
  { value: "ZA", label: "South Africa" },
  { value: "GH", label: "Ghana" },
  { value: "EG", label: "Egypt" },
  { value: "RW", label: "Rwanda" },
  { value: "TZ", label: "Tanzania" },
  { value: "UG", label: "Uganda" },
];

export function SignupPage() {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    email: "",
    password: "",
    full_name: "",
    job_title: "",
    company_name: "",
    country: "NG",
    sector: "fintech" as Sector,
    size: "small" as CompanySize,
    stage: "seed" as CompanyStage,
  });

  const update = <K extends keyof typeof form>(
    key: K,
    value: (typeof form)[K],
  ) => setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup(form);
      navigate("/onboarding", { replace: true });
    } catch (err) {
      setError(normalizeApiError(err).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-brand-50 p-6">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <img src="/logo.png" alt="CyberCapSec" className="h-14 w-14 mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-slate-900">
            Create your account
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Get a tailored security and compliance roadmap for your company.
          </p>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && <ErrorMessage message={error} />}

            <div>
              <h2 className="text-sm font-semibold text-slate-900 mb-3">
                About you
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Full name"
                  value={form.full_name}
                  onChange={(e) => update("full_name", e.target.value)}
                  required
                />
                <Input
                  label="Job title"
                  value={form.job_title}
                  onChange={(e) => update("job_title", e.target.value)}
                  placeholder="Founder, CTO, etc."
                />
                <Input
                  label="Work email"
                  type="email"
                  value={form.email}
                  onChange={(e) => update("email", e.target.value)}
                  required
                  autoComplete="email"
                  hint="Use your company email — Gmail, Yahoo, Outlook etc. are not accepted."
                />
                <Input
                  label="Password"
                  type="password"
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  required
                  autoComplete="new-password"
                  hint="At least 8 characters"
                />
              </div>
            </div>

            <div>
              <h2 className="text-sm font-semibold text-slate-900 mb-3">
                About your company
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Company name"
                  value={form.company_name}
                  onChange={(e) => update("company_name", e.target.value)}
                  required
                  className="sm:col-span-2"
                />
                <Select
                  label="Country"
                  value={form.country}
                  onChange={(e) => update("country", e.target.value)}
                  required
                >
                  {COUNTRY_OPTIONS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </Select>
                <Select
                  label="Sector"
                  value={form.sector}
                  onChange={(e) => update("sector", e.target.value as Sector)}
                  required
                >
                  {SECTOR_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </Select>
                <Select
                  label="Team size"
                  value={form.size}
                  onChange={(e) =>
                    update("size", e.target.value as CompanySize)
                  }
                  required
                >
                  {SIZE_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </Select>
                <Select
                  label="Stage"
                  value={form.stage}
                  onChange={(e) =>
                    update("stage", e.target.value as CompanyStage)
                  }
                  required
                >
                  {STAGE_OPTIONS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <Button type="submit" loading={loading} className="w-full" size="lg">
              Create account
            </Button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-600 mt-6">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-medium text-brand-600 hover:text-brand-700"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
