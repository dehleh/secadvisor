# CyberCapSec Advisory — Landing Site

Public marketing site for CyberCapSec Advisory. Static React + Vite + Tailwind,
deployed to Vercel.

## Sections

- Hero with primary "Start free assessment" CTA pointing to the dashboard signup
- Features (4 value props: 20-minute assessment, cross-framework propagation,
  10 policy templates, African-market-by-default)
- Frameworks (6-card grid showing SOC 2, NDPA, CBN, ISO 27001, POPIA, Kenya DPA)
- Pricing with currency switcher (NGN/KES/ZAR/GHS/USD) — auto-detects from
  browser timezone for African TZs, defaults to NGN
- FAQ (6 questions including the Vanta/Drata differentiation)
- Footer with legal + Paystack mention

## Local development

```bash
npm install
cp .env.example .env  # set VITE_APP_URL to your dashboard URL
npm run dev
```

## Deploy (Vercel)

```bash
vercel --prod
```

Set `VITE_APP_URL` in Vercel project settings to your production dashboard URL
(e.g. `https://app.cybercapsec.com`). All "Start free" / "Sign in" buttons
deep-link there.

## Structure

```
src/
  App.tsx          all sections in one file (~470 lines)
  main.tsx         entry point
  index.css        Tailwind base
  vite-env.d.ts    env type declarations
```

A single-file App is intentional for a landing page — easy to scan, easy to
hand to a designer for tweaks. When sections grow beyond what's manageable,
split each into `src/sections/`.

## Currency detection

The pricing section detects locale via `Intl.DateTimeFormat().resolvedOptions().timeZone`
and maps Lagos→NGN, Nairobi→KES, Johannesburg→ZAR, Accra→GHS. Everything else
defaults to NGN (because most early traffic is Nigerian and showing USD by
default would feel foreign). The user can switch currencies manually via the
toggle.

## Editing pricing

Pricing is defined in the `PRICING` constant in `App.tsx`. Keep it in sync
with the backend's `app/services/billing/catalog.py` — the landing page is
the marketing source of truth that visitors see, the backend catalog is
what they actually pay.
