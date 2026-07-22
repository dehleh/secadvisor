import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ClipboardCheck,
  Clock3,
  CreditCard,
  Database,
  FileQuestion,
  Globe,
  GraduationCap,
  Layers,
  LockKeyhole,
  Map,
  MessageSquareText,
  Route,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
  X,
} from "lucide-react";

// ----- Config ----------------------------------------------------------------

const APP_URL =
  (import.meta.env.VITE_APP_URL as string | undefined) ??
  "https://app.cybercapsec.com";

type Currency = "NGN" | "KES" | "ZAR" | "GHS" | "USD";

const CURRENCIES: Array<{ code: Currency; label: string; flag: string }> = [
  { code: "NGN", label: "Nigeria (NGN)", flag: "🇳🇬" },
  { code: "KES", label: "Kenya (KES)", flag: "🇰🇪" },
  { code: "ZAR", label: "South Africa (ZAR)", flag: "🇿🇦" },
  { code: "GHS", label: "Ghana (GHS)", flag: "🇬🇭" },
  { code: "USD", label: "Other (USD)", flag: "🌍" },
];

interface PricePoint {
  amount: number;
  symbol: string;
  locale: string;
  decimals: number;
}

const PRICING: Record<
  Currency,
  Record<"starter" | "growth" | "audit_ready", PricePoint>
> = {
  NGN: {
    starter: { amount: 40000, symbol: "₦", locale: "en-NG", decimals: 0 },
    growth: { amount: 100000, symbol: "₦", locale: "en-NG", decimals: 0 },
    audit_ready: { amount: 250000, symbol: "₦", locale: "en-NG", decimals: 0 },
  },
  KES: {
    starter: { amount: 1500, symbol: "KSh", locale: "en-KE", decimals: 0 },
    growth: { amount: 4500, symbol: "KSh", locale: "en-KE", decimals: 0 },
    audit_ready: { amount: 15000, symbol: "KSh", locale: "en-KE", decimals: 0 },
  },
  ZAR: {
    starter: { amount: 200, symbol: "R", locale: "en-ZA", decimals: 0 },
    growth: { amount: 600, symbol: "R", locale: "en-ZA", decimals: 0 },
    audit_ready: { amount: 2000, symbol: "R", locale: "en-ZA", decimals: 0 },
  },
  GHS: {
    starter: { amount: 150, symbol: "₵", locale: "en-GH", decimals: 0 },
    growth: { amount: 450, symbol: "₵", locale: "en-GH", decimals: 0 },
    audit_ready: { amount: 1500, symbol: "₵", locale: "en-GH", decimals: 0 },
  },
  USD: {
    starter: { amount: 10, symbol: "$", locale: "en-US", decimals: 0 },
    growth: { amount: 30, symbol: "$", locale: "en-US", decimals: 0 },
    audit_ready: { amount: 100, symbol: "$", locale: "en-US", decimals: 0 },
  },
};

function formatPrice(p: PricePoint): string {
  return `${p.symbol}${p.amount.toLocaleString(p.locale, {
    maximumFractionDigits: p.decimals,
  })}`;
}

function detectCurrencyFromBrowser(): Currency {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz.includes("Lagos")) return "NGN";
    if (tz.includes("Nairobi")) return "KES";
    if (tz.includes("Johannesburg")) return "ZAR";
    if (tz.includes("Accra")) return "GHS";
  } catch {
    // fall through
  }
  return "NGN";
}

// ----- Components ------------------------------------------------------------

function Header() {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-40 overflow-x-clip">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 md:h-16 flex items-center justify-between gap-3">
        <a href="/" className="flex min-w-0 items-center gap-2">
          <img src="/logo.png" alt="CyberCapSec" className="h-8 w-8 md:h-9 md:w-9" />
          <span className="truncate text-sm font-semibold text-slate-900 sm:text-base">
            CyberCapSec
          </span>
          <span className="hidden text-sm text-slate-500 sm:inline">Advisory</span>
        </a>
        <nav className="hidden md:flex items-center gap-4 text-sm lg:gap-6">
          <a
            href="#features"
            className="text-slate-700 hover:text-brand-600"
          >
            Features
          </a>
          <a href="#guided-flow" className="text-slate-700 hover:text-brand-600">
            How it guides
          </a>
          <a href="#pci-roadmap" className="text-slate-700 hover:text-brand-600">
            PCI DSS
          </a>
          <a
            href="#frameworks"
            className="text-slate-700 hover:text-brand-600"
          >
            Frameworks
          </a>
          <a href="#pricing" className="text-slate-700 hover:text-brand-600">
            Pricing
          </a>
          <a href="#faq" className="text-slate-700 hover:text-brand-600">
            FAQ
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <a
            href={`${APP_URL}/login`}
            className="hidden sm:inline-block text-sm text-slate-700 hover:text-brand-600 px-3 py-2"
          >
            Sign in
          </a>
          <a
            href="#pricing"
            className="whitespace-nowrap bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-3 sm:px-4 py-2 rounded-md"
          >
            View plans
          </a>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  const pathCards = [
    {
      label: "Client goal",
      text: "I need PCI DSS readiness",
      icon: CreditCard,
    },
    {
      label: "Guided scope",
      text: "Where does card data enter, move, or get stored?",
      icon: Map,
    },
    {
      label: "Roadmap",
      text: "Next 7 days, 30 days, 90 days, before validation",
      icon: Route,
    },
    {
      label: "Proof",
      text: "Evidence, policies, owners, and report language",
      icon: FileQuestion,
    },
  ];

  return (
    <section className="relative overflow-hidden bg-slate-950">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10 lg:py-12">
        <div className="grid gap-7 lg:grid-cols-[minmax(0,1.08fr)_minmax(280px,0.92fr)] lg:items-center">
          <div className="min-w-0 max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-sky-100 ring-1 ring-white/15">
              <Sparkles className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">Founder-friendly cybersecurity readiness</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight">
              Cybersecurity guidance a founder can actually follow.
            </h1>
            <p className="mt-4 max-w-2xl text-base sm:text-lg text-slate-300 leading-relaxed">
              CyberCapSec-Advisory turns goals like "I need PCI DSS," "a
              customer sent a security questionnaire," or "we need to reduce
              breach risk" into a plain-English readiness roadmap, evidence
              plan, policies, team owners, and shareable security posture
              report.
            </p>
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <a
                href="#pricing"
                className="inline-flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-medium px-5 py-3 rounded-lg text-base"
              >
                Choose a licence
                <ArrowRight className="h-4 w-4" />
              </a>
              <a
                href="#pci-roadmap"
                className="inline-flex items-center justify-center gap-2 bg-white/10 border border-white/20 hover:bg-white/15 text-white font-medium px-5 py-3 rounded-lg text-base"
              >
                See PCI DSS example
              </a>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {[
                ["PCI DSS readiness", "pci_dss"],
                ["Questionnaire", "questionnaire"],
                ["SOC 2 prep", "soc2"],
                ["Breach-risk reduction", "breach_risk"],
              ].map(([label, goal]) => (
                <a
                  key={goal}
                  href="#pricing"
                  className="rounded-full border border-white/15 bg-white/[0.06] px-3 py-1.5 text-xs sm:text-sm font-medium text-slate-200 hover:bg-white/10"
                >
                  {label}
                </a>
              ))}
            </div>
          </div>

          <div className="grid min-w-0 grid-cols-2 gap-3">
            {pathCards.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="min-w-0 rounded-lg border border-white/10 bg-white/[0.06] p-3 sm:p-4"
                >
                  <div className="flex min-w-0 items-center gap-2 text-sky-100">
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className="truncate text-[0.68rem] font-semibold uppercase tracking-wide sm:text-xs">
                      {item.label}
                    </span>
                  </div>
                  <p className="mt-2 break-words text-xs leading-5 text-slate-200 sm:mt-3 sm:text-sm sm:leading-6">
                    {item.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        <p className="mt-5 max-w-3xl text-sm leading-6 text-slate-400">
          Choose a paid licence to unlock workspace access. Built for African
          startups, fintechs, SaaS teams, and founders who need security
          clarity without jargon.
        </p>
      </div>
    </section>
  );
}

function GuidedFlow() {
  const steps = [
    {
      title: "Pick the security goal",
      body: "Start from the sentence a founder already has: PCI DSS, SOC 2, customer questionnaire, breach-risk reduction, payments, or privacy readiness.",
      icon: Sparkles,
    },
    {
      title: "Understand scope in plain English",
      body: "CyberCapSec asks the important questions first: what data is involved, which systems touch it, who has access, and what vendors are part of the flow.",
      icon: Map,
    },
    {
      title: "Get a readiness roadmap",
      body: "The app explains what to fix now, what can wait, who should own it, and which evidence proves the work was done.",
      icon: Route,
    },
    {
      title: "Answer with confidence",
      body: "Use policies, evidence, framework notes, and a security posture report to respond to customers, assessors, partners, or regulators.",
      icon: MessageSquareText,
    },
  ];

  return (
    <section id="guided-flow" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-12">
          <p className="text-sm font-semibold text-brand-700">
            Simpler, guided, educational
          </p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            The product starts from the founder's problem, not from a control
            catalog.
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            A client should not have to know the difference between scope,
            evidence, controls, and validation before taking action. CyberCapSec
            teaches the concept, then turns it into work.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div
                key={step.title}
                className="rounded-xl border border-slate-200 bg-slate-50 p-5"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-brand-700 shadow-sm">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-sm font-semibold text-slate-400">
                    0{index + 1}
                  </span>
                </div>
                <h3 className="mt-5 text-base font-semibold text-slate-900">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {step.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function PciInteractivePreview() {
  const [paymentFlow, setPaymentFlow] = useState("hosted");
  const [cardStorage, setCardStorage] = useState("no");
  const [staffAccess, setStaffAccess] = useState("limited");

  const scoreMap: Record<string, number> = {
    hosted: 90,
    embedded: 70,
    direct: 35,
    no: 90,
    tokens: 75,
    yes: 20,
    limited: 80,
    broad: 45,
    unknown: 30,
  };
  const score = Math.round(
    (scoreMap[paymentFlow] + scoreMap[cardStorage] + scoreMap[staffAccess]) / 3,
  );
  const label =
    score >= 80
      ? "Lower-scope starting point"
      : score >= 60
        ? "Needs scope confirmation"
        : "Scope before certification";
  const guidance =
    score >= 80
      ? "You may have a cleaner readiness path, but you still need provider proof, access reviews, logging checks, and evidence."
      : score >= 60
        ? "Clarify payment flows, logs, support access, and provider responsibility before promising a validation timeline."
        : "Start by reducing card-data exposure and mapping every system that can touch payment data.";

  return (
    <section className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-start">
          <div>
            <p className="text-sm font-semibold text-brand-700">
              Interactive PCI DSS preview
            </p>
            <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
              Let a founder understand PCI DSS scope in 30 seconds.
            </h2>
            <p className="mt-4 text-slate-600 text-lg leading-relaxed">
              This is the landing-page proof of the product promise: choose a
              few simple answers and see the likely readiness path immediately.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            {[
              {
                label: "How do card payments happen?",
                value: paymentFlow,
                setValue: setPaymentFlow,
                options: [
                  ["hosted", "Hosted checkout"],
                  ["embedded", "Embedded provider fields"],
                  ["direct", "Our app collects card details"],
                ],
              },
              {
                label: "Do you store card data?",
                value: cardStorage,
                setValue: setCardStorage,
                options: [
                  ["no", "No"],
                  ["tokens", "Tokens or masked data"],
                  ["yes", "Yes or not sure"],
                ],
              },
              {
                label: "Can staff access payment records?",
                value: staffAccess,
                setValue: setStaffAccess,
                options: [
                  ["limited", "Limited with MFA"],
                  ["broad", "Broad access"],
                  ["unknown", "Not sure"],
                ],
              },
            ].map((question) => (
              <div key={question.label} className="mb-5 last:mb-0">
                <h3 className="text-sm font-semibold text-slate-900">
                  {question.label}
                </h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {question.options.map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => question.setValue(value)}
                      className={
                        "rounded-md border px-3 py-2 text-sm font-medium transition " +
                        (question.value === value
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50")
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            ))}

            <div className="mt-6 rounded-lg border border-brand-200 bg-brand-50 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-brand-800">
                    Likely readiness path
                  </p>
                  <h3 className="mt-1 text-xl font-bold text-slate-900">
                    {label}
                  </h3>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-slate-900">
                    {score}
                  </div>
                  <div className="text-xs text-slate-500">scope clarity</div>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-700">
                {guidance}
              </p>
              <a
                href={`${APP_URL}/signup?goal=pci_dss`}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                Start PCI DSS readiness
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function PciRoadmap() {
  const phases = [
    {
      title: "Map payment scope",
      body: "Find where card data enters, moves, gets stored, appears in logs, or can be accessed by staff and vendors.",
      evidence: "Payment data flow, provider contract, scoped asset list",
      icon: CreditCard,
    },
    {
      title: "Reduce card-data exposure",
      body: "Use hosted payment pages or tokenized provider flows where possible, then isolate payment-impacting systems.",
      evidence: "Payment architecture note, data minimization decision",
      icon: Database,
    },
    {
      title: "Harden access and systems",
      body: "Enforce MFA, least privilege, patching, vulnerability scans, secure release checks, logging, and incident response.",
      evidence: "MFA proof, access review, scan result, incident plan",
      icon: LockKeyhole,
    },
    {
      title: "Prepare validation proof",
      body: "Collect evidence, assign owners, document exceptions, and know what remains before an assessor or payment partner reviews it.",
      evidence: "Evidence tracker, exception log, readiness report",
      icon: FileQuestion,
    },
  ];

  return (
    <section id="pci-roadmap" className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <p className="text-sm font-semibold text-brand-700">
              PCI DSS example
            </p>
            <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
              From "I need PCI DSS" to a readiness roadmap.
            </h2>
            <p className="mt-4 text-slate-600 text-lg leading-relaxed">
              CyberCapSec-Advisory explains PCI DSS like a security coach: what
              is in scope, what creates payment risk, what should be fixed
              first, and what evidence proves readiness. The same guided pattern
              applies to SOC 2, ISO 27001, NIST CSF, CIS Controls, NDPA, CBN,
              POPIA, Kenya DPA, GDPR, and HIPAA.
            </p>
            <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
              <h3 className="font-semibold text-slate-900">
                Founder translation
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                PCI DSS is not just a certificate. It is a way to prove payment
                card data is scoped, minimized, protected, monitored, and ready
                for the right validation path.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {phases.map((phase, index) => {
              const Icon = phase.icon;
              return (
                <div
                  key={phase.title}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
                >
                  <div className="flex gap-4">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-100 text-brand-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-600">
                          Phase {index + 1}
                        </span>
                        <span className="text-xs font-medium text-slate-500">
                          Readiness roadmap
                        </span>
                      </div>
                      <h3 className="mt-2 font-semibold text-slate-900">
                        {phase.title}
                      </h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">
                        {phase.body}
                      </p>
                      <p className="mt-3 text-xs leading-5 text-slate-500">
                        Evidence: {phase.evidence}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function WhoItsFor() {
  const audiences = [
    {
      title: "Fintech taking payments",
      body: "Needs PCI DSS clarity, payment data-flow mapping, access hardening, and evidence customers or partners will trust.",
      icon: CreditCard,
    },
    {
      title: "SaaS selling to enterprise",
      body: "Needs SOC 2-style answers, customer questionnaire support, security policies, and posture reports.",
      icon: MessageSquareText,
    },
    {
      title: "Health, finance, or data-heavy startup",
      body: "Needs a practical view of sensitive data, vendor access, incident response, privacy, and cyber resilience.",
      icon: Database,
    },
    {
      title: "Founder under review pressure",
      body: "Needs to understand what to fix now, what evidence is missing, and how to explain open risks honestly.",
      icon: Users,
    },
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-12">
          <p className="text-sm font-semibold text-brand-700">Who it is for</p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Built for teams that need security clarity before security headcount.
          </h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {audiences.map((audience) => {
            const Icon = audience.icon;
            return (
              <div key={audience.title} className="rounded-xl border border-slate-200 bg-slate-50 p-5">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-white text-brand-700 shadow-sm">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900">
                  {audience.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {audience.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function SampleReports() {
  const reports = [
    {
      title: "PCI DSS readiness report",
      body: "Payment scope, card-data exposure, access controls, logging, vulnerability management, evidence gaps, and validation notes.",
      sections: ["Scope", "Payment risks", "Evidence", "Validation path"],
    },
    {
      title: "SOC 2 readiness report",
      body: "Trust controls across access, change management, vendors, incidents, monitoring, resilience, and evidence history.",
      sections: ["Trust story", "Control gaps", "Roadmap", "Proof status"],
    },
    {
      title: "Cyber posture report",
      body: "Plain-English risk register, first actions, team owners, policy status, evidence maturity, and shareable posture summary.",
      sections: ["Top risks", "Owners", "Timeline", "Report link"],
    },
  ];

  return (
    <section className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-12">
          <p className="text-sm font-semibold text-brand-700">
            See the output before signing up
          </p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Sample readiness reports make the value tangible.
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            Buyers should not have to imagine what CyberCapSec produces. The
            product turns security work into reports that founders, customers,
            assessors, and leadership can understand.
          </p>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          {reports.map((report) => (
            <div key={report.title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <FileQuestion className="h-6 w-6 text-brand-700" />
              <h3 className="mt-4 text-lg font-semibold text-slate-900">
                {report.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {report.body}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {report.sections.map((section) => (
                  <span key={section} className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                    {section}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FrameworkComparison() {
  const rows = [
    ["PCI DSS", "Payment card security", "Scope payment flows and prove card-data controls."],
    ["SOC 2", "Customer trust", "Show customers that security controls operate consistently."],
    ["ISO 27001", "Security management system", "Run risk treatment, ownership, reviews, and improvement."],
    ["NIST CSF", "Cyber risk baseline", "Communicate governance, protection, detection, response, and recovery."],
    ["CIS Controls", "Technical safeguards", "Prioritize practical defenses engineers can implement."],
    ["NDPA / GDPR / POPIA / Kenya DPA", "Privacy readiness", "Connect personal-data obligations to security controls and evidence."],
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-10">
          <p className="text-sm font-semibold text-brand-700">
            Choose the right path
          </p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Frameworks should be compared in human language.
          </h2>
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          {rows.map(([framework, purpose, action]) => (
            <div key={framework} className="grid gap-3 border-b border-slate-200 p-4 last:border-b-0 md:grid-cols-[220px_240px_1fr]">
              <div className="font-semibold text-slate-900">{framework}</div>
              <div className="text-sm font-medium text-brand-700">{purpose}</div>
              <div className="text-sm leading-6 text-slate-600">{action}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrustProof() {
  const proofs = [
    "Example policy pack for access, incidents, data protection, vendors, backups, and change management.",
    "Evidence checklist for MFA, access reviews, payment data flows, scans, restore tests, and vendor reviews.",
    "Roadmap grouped by next 7 days, 30 days, 90 days, and before audit or customer review.",
    "Methodology note: security fundamentals first, framework mapping second, certification by qualified reviewers.",
  ];

  return (
    <section className="py-20 bg-slate-950">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <p className="text-sm font-semibold text-sky-200">Trust proof</p>
            <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-white">
              Clear about what the product does, and what it does not do.
            </h2>
            <p className="mt-4 text-slate-300 text-lg leading-relaxed">
              CyberCapSec-Advisory helps teams get ready. It does not replace a
              PCI assessor, SOC 2 auditor, ISO certification body, or legal
              advisor. That honesty builds trust.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {proofs.map((proof) => (
              <div key={proof} className="rounded-xl border border-white/10 bg-white/[0.06] p-4">
                <Check className="h-5 w-5 text-emerald-300" />
                <p className="mt-3 text-sm leading-6 text-slate-200">
                  {proof}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function Features() {
  const items = [
    {
      icon: ClipboardCheck,
      title: "20-minute cyber posture assessment",
      body: "Answer practical questions about identity, cloud, applications, data, people, vendors, resilience, and response. The platform turns them into a 13-week risk-ranked roadmap.",
    },
    {
      icon: Zap,
      title: "5-minute founder baseline",
      body: "Start light when the team is busy. The quick baseline explains the first security gaps before the founder commits to the full assessment.",
    },
    {
      icon: BookOpen,
      title: "PCI DSS and framework guides",
      body: "Understand scope, readiness phases, evidence, owner actions, and common traps for PCI DSS, SOC 2, ISO 27001, NIST CSF, CIS Controls, NDPA, CBN, and privacy paths.",
    },
    {
      icon: Layers,
      title: "Evidence that proves real security work",
      body: "Attach links, screenshots, policy references, and narratives to controls. One strong evidence item can support several security domains and mapped compliance frameworks.",
    },
    {
      icon: MessageSquareText,
      title: "Security questionnaire assistant",
      body: "Draft clear customer-security answers from your controls, roadmap, evidence, and framework readiness language instead of improvising under deadline pressure.",
    },
    {
      icon: ShieldCheck,
      title: "Policies tied to operational risk",
      body: "Generate access control, incident response, vendor risk, backup, change management, awareness, and data protection policies that help teams behave securely.",
    },
    {
      icon: Globe,
      title: "African market by default",
      body: "Pricing in your local currency, NDPC's 72-hour breach clock, CBN's 24-hour reporting, Paystack billing. We assume Lagos, not San Francisco.",
    },
  ];
  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-2xl mb-14">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Everything an early-stage cybersecurity program needs
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            Built by people who shipped fintech in Nigeria, Kenya, and South
            Africa. We know what attackers exploit, what customers ask for, and
            what regulators actually care about.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="bg-slate-50 border border-slate-200 rounded-xl p-6"
              >
                <div className="h-10 w-10 rounded-lg bg-brand-100 text-brand-700 flex items-center justify-center mb-4">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900 text-lg mb-2">
                  {item.title}
                </h3>
                <p className="text-slate-600 leading-relaxed">{item.body}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Frameworks() {
  const frameworks = [
    {
      code: "PCI DSS",
      desc: "Payment card security readiness",
      question: "Where does card data enter, move, get stored, or appear in logs?",
      path: "Scope payments, reduce exposure, harden access, collect validation evidence.",
    },
    {
      code: "SOC 2",
      desc: "Customer trust and security operations",
      question: "Can you prove your controls operated consistently over time?",
      path: "Build access, change, incident, vendor, and evidence habits customers trust.",
    },
    {
      code: "ISO 27001",
      desc: "Information security management system",
      question: "Do you manage security risk as a repeatable business process?",
      path: "Run risk treatment, policies, owners, reviews, and improvement cycles.",
    },
    {
      code: "NIST CSF",
      desc: "Cybersecurity risk-management baseline",
      question: "Can leadership see how you govern, protect, detect, respond, and recover?",
      path: "Create a security baseline before choosing a formal certification path.",
    },
    {
      code: "CIS Controls",
      desc: "Practical technical safeguards",
      question: "Do you know what you own, who can access it, and whether it is monitored?",
      path: "Prioritize asset inventory, access, configuration, vulnerabilities, and logs.",
    },
    {
      code: "NDPA",
      desc: "Nigeria data-protection readiness",
      question: "Can you show how personal data is collected, protected, shared, and deleted?",
      path: "Map personal data, secure access, manage vendors, and prepare incidents.",
    },
    {
      code: "CBN",
      desc: "Financial-sector cybersecurity readiness",
      question: "Can leadership see cyber risks, controls, incidents, vendors, and resilience?",
      path: "Show governance, monitoring, third-party risk, reporting, and recovery readiness.",
    },
    {
      code: "POPIA",
      desc: "South Africa privacy readiness",
      question: "Are privacy promises backed by real security controls and vendor oversight?",
      path: "Connect privacy obligations to access, retention, vendor, and incident evidence.",
    },
    {
      code: "Kenya DPA",
      desc: "Kenya data-protection readiness",
      question: "Do you understand data flows, retention, access, vendors, and breach response?",
      path: "Turn data-protection expectations into a clear operating roadmap.",
    },
  ];
  return (
    <section id="frameworks" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-14">
          <p className="text-sm font-semibold text-brand-700">
            Common framework guides
          </p>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Frameworks explained before they become work
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            A client should understand the security meaning of a framework in
            minutes: the first readiness question, the likely roadmap, and the
            evidence they will need before talking to customers, assessors, or
            regulators.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {frameworks.map((fw) => (
            <div
              key={fw.code}
              className="bg-slate-50 border border-slate-200 rounded-xl p-5 hover:border-brand-300 hover:shadow-sm transition"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="font-semibold text-slate-900">{fw.code}</div>
                <BookOpen className="h-4 w-4 text-brand-700" />
              </div>
              <div className="text-sm text-slate-600 mt-1">{fw.desc}</div>
              <div className="mt-4 rounded-lg bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  First question
                </p>
                <p className="mt-1 text-sm leading-6 text-slate-700">
                  {fw.question}
                </p>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-700">
                {fw.path}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function EducationLayer() {
  const items = [
    {
      title: "Plain-English glossary",
      body: "Explain CDE, MFA, least privilege, vulnerability management, incident response, evidence, and exceptions without making the founder feel behind.",
      icon: GraduationCap,
    },
    {
      title: "Evidence examples",
      body: "Show what good proof looks like: MFA screenshots, access reviews, payment data flows, backup restore tests, vendor reviews, and incident tabletop notes.",
      icon: ClipboardCheck,
    },
    {
      title: "Customer questionnaire help",
      body: "Draft clear answers using the company's actual policies, roadmap, evidence, and framework-readiness state.",
      icon: MessageSquareText,
    },
    {
      title: "Owner-ready tasks",
      body: "Roadmap items explain why the work matters, how a founder should think about it, how an engineer fixes it, and what evidence closes it.",
      icon: Users,
    },
    {
      title: "Timeline clarity",
      body: "Separate next 7 days, next 30 days, next 90 days, and before-audit work so teams know what to do first.",
      icon: Clock3,
    },
    {
      title: "Security first, compliance mapped",
      body: "The workflow covers identity, cloud, application security, data protection, vendors, people, response, and resilience before mapping to frameworks.",
      icon: ShieldCheck,
    },
  ];

  return (
    <section className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-3xl mb-12">
          <p className="text-sm font-semibold text-brand-700">
            Built to teach while it guides
          </p>
          <h2 className="mt-3 text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Founder-friendly does not mean shallow.
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            CyberCapSec should help non-security founders understand what
            matters, while still giving security and engineering teams enough
            structure to execute properly.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.title} className="rounded-xl bg-white p-5 border border-slate-200">
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-700">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {item.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

interface PricingTierConfig {
  tier: "starter" | "growth" | "audit_ready";
  name: string;
  blurb: string;
  features: { included: boolean; text: string }[];
  cta: string;
  highlighted?: boolean;
}

function Pricing() {
  const [currency, setCurrency] = useState<Currency>("NGN");

  useEffect(() => {
    setCurrency(detectCurrencyFromBrowser());
  }, []);

  const tiers: PricingTierConfig[] = [
    {
      tier: "starter",
      name: "Starter",
      blurb: "Solo founder building a real program.",
      features: [
        { included: true, text: "4 active assessments" },
        { included: true, text: "25 evidence items" },
        { included: true, text: "5 published policies" },
        { included: true, text: "2 frameworks of your choice" },
        { included: true, text: "AI advisor (Claude)" },
        { included: false, text: "All frameworks" },
      ],
      cta: "Start with Starter",
    },
    {
      tier: "growth",
      name: "Growth",
      blurb: "The right answer for most fintechs.",
      features: [
        { included: true, text: "Unlimited assessments" },
        { included: true, text: "Unlimited evidence" },
        { included: true, text: "Unlimited policies" },
        { included: true, text: "All common framework guides" },
        { included: true, text: "AI advisor (Claude)" },
        { included: true, text: "Priority support" },
      ],
      cta: "Start with Growth",
      highlighted: true,
    },
    {
      tier: "audit_ready",
      name: "Audit-Ready",
      blurb: "Going into PCI DSS, SOC 2, ISO, or customer review pressure.",
      features: [
        { included: true, text: "Everything in Growth" },
        { included: true, text: "Dedicated reviewer" },
        { included: true, text: "Readiness prep workshop" },
        { included: true, text: "Custom policy drafting" },
        { included: true, text: "Pre-review walkthrough" },
        { included: true, text: "Direct messaging" },
      ],
      cta: "Talk to us",
    },
  ];

  return (
    <section id="pricing" className="py-12 md:py-16 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="max-w-2xl mb-10">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Pricing in your currency
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            We bill in NGN, KES, ZAR, GHS, and USD via Paystack. No surprise
            bank charges, no FX markup, no Stripe-routing-through-Ireland fees.
          </p>
        </div>

        <div className="mb-8 flex max-w-full flex-wrap items-center gap-2 rounded-lg bg-slate-100 p-1 sm:inline-flex">
          {CURRENCIES.map((c) => (
            <button
              key={c.code}
              onClick={() => setCurrency(c.code)}
              className={
                "shrink-0 px-3 py-1.5 text-sm rounded-md transition " +
                (currency === c.code
                  ? "bg-white text-slate-900 shadow-sm font-medium"
                  : "text-slate-600 hover:text-slate-900")
              }
            >
              <span className="mr-1">{c.flag}</span> {c.code}
            </button>
          ))}
        </div>

        <div className="grid min-w-0 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tiers.map((tier) => {
            const price = PRICING[currency][tier.tier];
            return (
              <div
                key={tier.tier}
                className={
                  "min-w-0 bg-white border rounded-xl p-5 sm:p-6 flex flex-col " +
                  (tier.highlighted
                    ? "border-brand-500 shadow-lg ring-1 ring-brand-500"
                    : "border-slate-200")
                }
              >
                {tier.highlighted && (
                  <div className="-mt-9 mb-4 self-start bg-brand-600 text-white text-xs font-semibold uppercase tracking-wide px-3 py-1 rounded-full">
                    Most popular
                  </div>
                )}
                <h3 className="font-semibold text-slate-900 text-lg">
                  {tier.name}
                </h3>
                <p className="text-sm text-slate-600 mt-1 min-h-[2.5rem]">
                  {tier.blurb}
                </p>
                <div className="my-5">
                  <div className="text-2xl font-bold text-slate-900 sm:text-3xl">
                    {formatPrice(price)}
                  </div>
                  <div className="text-sm text-slate-500 mt-0.5">
                    per month
                  </div>
                </div>
                <ul className="space-y-2 mb-6 flex-1">
                  {tier.features.map((f, i) => (
                    <li
                      key={i}
                      className="min-w-0 flex items-start gap-2 text-sm"
                    >
                      {f.included ? (
                        <Check className="h-4 w-4 mt-0.5 text-emerald-500 shrink-0" />
                      ) : (
                        <X className="h-4 w-4 mt-0.5 text-slate-300 shrink-0" />
                      )}
                      <span
                        className={
                          f.included
                            ? "min-w-0 break-words text-slate-700"
                            : "min-w-0 break-words text-slate-400"
                        }
                      >
                        {f.text}
                      </span>
                    </li>
                  ))}
                </ul>
                <a
                  href={
                    tier.tier === "audit_ready"
                      ? "mailto:hello@cybercapsec.com?subject=Audit-Ready%20plan%20enquiry"
                      : `${APP_URL}/signup`
                  }
                  className={
                    "block text-center font-medium py-2.5 rounded-md transition " +
                    (tier.highlighted
                      ? "bg-brand-600 hover:bg-brand-700 text-white"
                      : "bg-slate-100 hover:bg-slate-200 text-slate-900")
                  }
                >
                  {tier.cta}
                </a>
              </div>
            );
          })}
        </div>

        <p className="text-center text-sm text-slate-500 mt-8">
          All paid plans bill monthly. Cancel any time. Annual billing coming
          soon.
        </p>
      </div>
    </section>
  );
}

function FAQ() {
  const items = [
    {
      q: "Will CyberCapSec certify us for PCI DSS or SOC 2?",
      a: "No. CyberCapSec-Advisory helps you understand readiness, scope the work, close security gaps, collect evidence, and prepare for the right validation path. Final certification, audit, or validation still depends on the relevant assessor, auditor, payment partner, or regulator.",
    },
    {
      q: "Can a non-security founder understand PCI DSS with this?",
      a: "That is the point. The product starts with plain questions: how payments happen, whether card data is stored, who can access payment systems, whether logs might contain sensitive data, and what proof is needed. Then it turns the answers into a readiness roadmap.",
    },
    {
      q: "Is this only a compliance product?",
      a: "No. Compliance mapping is included, but the core workflow is cybersecurity: identity and access, cloud infrastructure, application security, data protection, vendor risk, incident response, people, and resilience. Frameworks sit on top of that real security work.",
    },
    {
      q: "How is this different from Vanta or Drata?",
      a: "Vanta and Drata are strong automation platforms. CyberCapSec-Advisory is positioned as a guided cybersecurity advisor for founders and African startups: simpler language, local pricing, African regulatory context, readiness education, and a roadmap that explains what to do before automation becomes useful.",
    },
    {
      q: "Who reads the data we put in?",
      a: "Your data stays in your tenant. The AI advisor sends sanitised assessment summaries to Anthropic's Claude API to generate your report — no customer-identifiable data leaves the platform without your action. We retain audit logs of all access. Full data processing details on request.",
    },
    {
      q: "Do users need to pay before accessing the workspace?",
      a: "Yes. Guided assessments, PCI DSS and other readiness roadmaps, evidence, policies, reports, learning paths, and team access require a paid licence.",
    },
    {
      q: "What does the readiness prep workshop actually cover?",
      a: "A working session before your customer review, PCI DSS validation, SOC 2 audit, ISO certification path, or regulator conversation. We review your scope, evidence, policies, roadmap, open risks, and likely questions, then produce a short readiness memo.",
    },
    {
      q: "Do you offer custom pricing for groups, accelerators, or VCs?",
      a: "Yes. If you're an accelerator, VC, or industry body wanting to provide CyberCapSec Advisory to a portfolio or membership, email hello@cybercapsec.com.",
    },
  ];
  return (
    <section id="faq" className="py-20 bg-slate-50 border-t border-slate-200">
      <div className="max-w-3xl mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 mb-10">
          Frequently asked
        </h2>
        <div className="space-y-4">
          {items.map((item, i) => (
            <details
              key={i}
              className="group bg-white border border-slate-200 rounded-lg overflow-hidden"
            >
              <summary className="flex items-center justify-between cursor-pointer px-5 py-4 font-medium text-slate-900 hover:bg-slate-50">
                {item.q}
                <span className="text-slate-400 group-open:rotate-180 transition-transform">
                  ↓
                </span>
              </summary>
              <div className="px-5 pb-4 text-slate-600 leading-relaxed">
                {item.a}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="py-20 bg-gradient-to-br from-brand-600 to-brand-900">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
          Ready to make cybersecurity clear enough to act on?
        </h2>
        <p className="mt-4 text-brand-100 text-lg max-w-2xl mx-auto">
          Choose a licence, start with a guided baseline, understand your
          readiness path, and turn security goals into roadmap tasks, evidence,
          owners, and reports.
        </p>
        <a
          href="#pricing"
          className="inline-flex items-center justify-center gap-2 mt-8 bg-white hover:bg-slate-50 text-brand-700 font-semibold px-6 py-3 rounded-lg text-base"
        >
          View licence options
          <ArrowRight className="h-4 w-4" />
        </a>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-12">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <img
                src="/logo.png"
                alt="CyberCapSec"
                className="h-9 w-9 bg-white rounded-md p-0.5"
              />
              <span className="font-semibold text-white">CyberCapSec</span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              AI-powered cybersecurity advisory for African startups, with
              compliance mapping built in.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm mb-3">Product</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#features" className="hover:text-white">Features</a>
              </li>
              <li>
                <a href="#frameworks" className="hover:text-white">Frameworks</a>
              </li>
              <li>
                <a href="#pricing" className="hover:text-white">Pricing</a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm mb-3">Company</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="mailto:hello@cybercapsec.com" className="hover:text-white">
                  hello@cybercapsec.com
                </a>
              </li>
              <li>
                <a href="/privacy" className="hover:text-white">Privacy</a>
              </li>
              <li>
                <a href="/terms" className="hover:text-white">Terms</a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-white text-sm mb-3">For users</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href={`${APP_URL}/login`} className="hover:text-white">
                  Sign in
                </a>
              </li>
              <li>
                <a href={`${APP_URL}/signup`} className="hover:text-white">
                  Sign up
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-slate-800 text-sm text-slate-500 flex flex-col md:flex-row justify-between gap-3">
          <div>© {new Date().getFullYear()} CyberCapSec Ltd. All rights reserved.</div>
          <div>
            Payments via{" "}
            <a
              href="https://paystack.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white"
            >
              Paystack
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function App() {
  return (
    <div className="min-h-screen overflow-x-hidden bg-white text-slate-900">
      <Header />
      <main className="overflow-x-hidden">
        <Hero />
        <GuidedFlow />
        <PciInteractivePreview />
        <PciRoadmap />
        <WhoItsFor />
        <SampleReports />
        <Features />
        <FrameworkComparison />
        <Frameworks />
        <EducationLayer />
        <TrustProof />
        <Pricing />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
