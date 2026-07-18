import { useEffect, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  ClipboardCheck,
  Globe,
  Layers,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
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
    starter: { amount: 15000, symbol: "₦", locale: "en-NG", decimals: 0 },
    growth: { amount: 45000, symbol: "₦", locale: "en-NG", decimals: 0 },
    audit_ready: { amount: 150000, symbol: "₦", locale: "en-NG", decimals: 0 },
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
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <a href="/" className="flex items-center gap-2">
          <img src="/logo.png" alt="CyberCapSec" className="h-9 w-9" />
          <span className="font-semibold text-slate-900">CyberCapSec</span>
          <span className="text-slate-500 text-sm">Advisory</span>
        </a>
        <nav className="hidden md:flex items-center gap-6 text-sm">
          <a
            href="#features"
            className="text-slate-700 hover:text-brand-600"
          >
            Features
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
            href={`${APP_URL}/signup`}
            className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-md"
          >
            Start free
          </a>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-slate-50 via-brand-50 to-white" />
      <div className="max-w-6xl mx-auto px-6 py-20 md:py-28">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-brand-100 px-3 py-1 text-xs font-medium text-brand-700 mb-6">
            <Sparkles className="h-3.5 w-3.5" />
            Built for African fintechs and SaaS
          </div>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-slate-900 leading-[1.05]">
            Run your cybersecurity program, not just your{" "}
            <span className="text-brand-600">compliance checklist</span>.
          </h1>
          <p className="mt-6 text-lg md:text-xl text-slate-600 leading-relaxed max-w-2xl">
            CyberCapSec Advisory helps startups in Lagos, Nairobi, Joburg, and
            Accra assess cyber risk, prioritize controls, collect evidence,
            publish policies, and share a credible posture report. Guided
            readiness for PCI DSS, SOC 2, ISO 27001, NIST CSF, CIS Controls,
            NDPA, CBN, POPIA, and Kenya DPA comes with it.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <a
              href={`${APP_URL}/signup`}
              className="inline-flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-medium px-6 py-3 rounded-lg text-base"
            >
              Start free baseline
              <ArrowRight className="h-4 w-4" />
            </a>
            <a
              href="#pricing"
              className="inline-flex items-center justify-center gap-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-900 font-medium px-6 py-3 rounded-lg text-base"
            >
              See pricing
            </a>
          </div>
          <p className="mt-4 text-sm text-slate-500">
            No credit card required. NGN, KES, ZAR, GHS, or USD billing via
            Paystack.
          </p>
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
      path: "Scope payments, harden systems, collect evidence, prepare validation.",
    },
    {
      code: "SOC 2",
      desc: "Customer trust and security operations",
      path: "Build controls, operate them consistently, package auditor-ready proof.",
    },
    {
      code: "ISO 27001",
      desc: "Information security management system",
      path: "Run risk treatment, policies, ownership, reviews, and improvement.",
    },
    {
      code: "NIST CSF",
      desc: "Cybersecurity risk-management baseline",
      path: "Govern, identify, protect, detect, respond, and recover with clarity.",
    },
    {
      code: "CIS Controls",
      desc: "Practical technical safeguards",
      path: "Prioritize assets, access, configuration, vulnerability fixes, and logs.",
    },
    {
      code: "NDPA",
      desc: "Nigeria data-protection readiness",
      path: "Map personal data, secure access, manage vendors, and prepare incidents.",
    },
    {
      code: "CBN",
      desc: "Financial-sector cybersecurity readiness",
      path: "Show governance, resilience, monitoring, third-party risk, and reporting.",
    },
    {
      code: "POPIA",
      desc: "South Africa privacy readiness",
      path: "Connect privacy obligations to real security controls and evidence.",
    },
    {
      code: "Kenya DPA",
      desc: "Kenya data-protection readiness",
      path: "Track data flows, retention, access, vendors, and breach response.",
    },
  ];
  return (
    <section id="frameworks" className="py-20 bg-slate-50 border-y border-slate-200">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-2xl mb-14">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Frameworks explained before they become work
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            A client who needs PCI DSS, SOC 2, ISO 27001, NIST CSF, CIS
            Controls, NDPA, CBN, POPIA, or Kenya DPA should understand the path
            in minutes: what it is for, what to fix first, what evidence to
            collect, and what readiness looks like.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {frameworks.map((fw) => (
            <div
              key={fw.code}
              className="bg-white border border-slate-200 rounded-lg p-5 hover:border-brand-300 hover:shadow-sm transition"
            >
              <div className="font-semibold text-slate-900">{fw.code}</div>
              <div className="text-sm text-slate-600 mt-1">{fw.desc}</div>
              <p className="mt-3 text-sm leading-6 text-slate-700">{fw.path}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

interface PricingTierConfig {
  tier: "free" | "starter" | "growth" | "audit_ready";
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
      tier: "free",
      name: "Free",
      blurb: "See the platform without putting in a card.",
      features: [
        { included: true, text: "1 active assessment" },
        { included: true, text: "3 evidence items" },
        { included: true, text: "1 published policy" },
        { included: true, text: "NDPA + 1 framework" },
        { included: false, text: "AI advisor" },
        { included: false, text: "Unlimited assessments" },
      ],
      cta: "Start free",
    },
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
        { included: true, text: "All 6 frameworks" },
        { included: true, text: "AI advisor (Claude)" },
        { included: true, text: "Priority support" },
      ],
      cta: "Start with Growth",
      highlighted: true,
    },
    {
      tier: "audit_ready",
      name: "Audit-Ready",
      blurb: "Going into a SOC 2 audit in 90 days.",
      features: [
        { included: true, text: "Everything in Growth" },
        { included: true, text: "Dedicated reviewer" },
        { included: true, text: "Audit prep workshop" },
        { included: true, text: "Custom policy drafting" },
        { included: true, text: "Pre-audit walkthrough" },
        { included: true, text: "Direct messaging" },
      ],
      cta: "Talk to us",
    },
  ];

  return (
    <section id="pricing" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-6">
        <div className="max-w-2xl mb-10">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900">
            Pricing in your currency
          </h2>
          <p className="mt-4 text-slate-600 text-lg">
            We bill in NGN, KES, ZAR, GHS, and USD via Paystack. No surprise
            bank charges, no FX markup, no Stripe-routing-through-Ireland fees.
          </p>
        </div>

        <div className="mb-8 inline-flex items-center gap-2 bg-slate-100 p-1 rounded-lg">
          {CURRENCIES.map((c) => (
            <button
              key={c.code}
              onClick={() => setCurrency(c.code)}
              className={
                "px-3 py-1.5 text-sm rounded-md transition " +
                (currency === c.code
                  ? "bg-white text-slate-900 shadow-sm font-medium"
                  : "text-slate-600 hover:text-slate-900")
              }
            >
              <span className="mr-1">{c.flag}</span> {c.code}
            </button>
          ))}
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tiers.map((tier) => {
            const price =
              tier.tier === "free"
                ? null
                : PRICING[currency][
                    tier.tier as "starter" | "growth" | "audit_ready"
                  ];
            return (
              <div
                key={tier.tier}
                className={
                  "bg-white border rounded-xl p-6 flex flex-col " +
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
                  {price === null ? (
                    <>
                      <div className="text-3xl font-bold text-slate-900">
                        Free
                      </div>
                      <div className="text-sm text-slate-500 mt-0.5">
                        forever
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="text-3xl font-bold text-slate-900">
                        {formatPrice(price)}
                      </div>
                      <div className="text-sm text-slate-500 mt-0.5">
                        per month
                      </div>
                    </>
                  )}
                </div>
                <ul className="space-y-2 mb-6 flex-1">
                  {tier.features.map((f, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm"
                    >
                      {f.included ? (
                        <Check className="h-4 w-4 mt-0.5 text-emerald-500 shrink-0" />
                      ) : (
                        <X className="h-4 w-4 mt-0.5 text-slate-300 shrink-0" />
                      )}
                      <span
                        className={
                          f.included ? "text-slate-700" : "text-slate-400"
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
      q: "Is this a replacement for a SOC 2 auditor?",
      a: "No. CyberCapSec Advisory gets you ready for an audit. You'll still need a licensed audit firm to issue the SOC 2 report. We help you build the program, draft the policies, collect the evidence, and walk in confident.",
    },
    {
      q: "How is this different from Vanta or Drata?",
      a: "Vanta and Drata are excellent products built for the US market. They charge USD pricing, integrate primarily with US-shaped SaaS, and don't model African regulators (NDPC, CBN, ODPC, Information Regulator). We're built African-first: NGN/KES/ZAR/GHS billing via Paystack, NDPA + CBN + POPIA + Kenya DPA in the core data model, paraphrased control text grounded in regulators we've actually read.",
    },
    {
      q: "Who reads the data we put in?",
      a: "Your data stays in your tenant. The AI advisor sends sanitised assessment summaries to Anthropic's Claude API to generate your report — no customer-identifiable data leaves the platform without your action. We retain audit logs of all access. Full data processing details on request.",
    },
    {
      q: "What does the free tier let me do?",
      a: "Run one assessment, see your AI-generated risk register and 13-week roadmap, store up to 3 pieces of evidence, publish 1 policy, work in NDPA plus one other framework. It's enough to evaluate the platform; not enough to run a full SOC 2 prep. Upgrade to Starter or Growth when you outgrow it.",
    },
    {
      q: "What does the audit prep workshop in Audit-Ready actually cover?",
      a: "A 90-minute working session before your audit kickoff: walk through your evidence with an experienced reviewer, identify gaps the platform might have missed, dry-run the auditor questions you'll get, and prioritise the last 2-3 weeks before fieldwork. Includes a written readiness memo.",
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
          Ready to put real numbers on your cyber risk?
        </h2>
        <p className="mt-4 text-brand-100 text-lg max-w-2xl mx-auto">
          The free assessment takes 20 minutes and produces a risk-ranked
          security roadmap. No credit card. No sales call.
        </p>
        <a
          href={`${APP_URL}/signup`}
          className="inline-flex items-center justify-center gap-2 mt-8 bg-white hover:bg-slate-50 text-brand-700 font-semibold px-6 py-3 rounded-lg text-base"
        >
          Start free assessment
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
    <>
      <Header />
      <main>
        <Hero />
        <Features />
        <Frameworks />
        <Pricing />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </>
  );
}
