# CyberCapSec Advisory — Backend API

AI-powered security and compliance advisory platform for African startups and SMEs.

## What it does

Companies onboard, complete a structured security & compliance assessment, and receive:

- AI-generated executive summary, risk register, and 13-week roadmap ✅ Session 3
- SOC 2 readiness score and gap analysis ✅ Session 2
- NDPA / CBN / NITDA / POPIA / Kenya DPA compliance gap analysis ✅ Session 2
- Cross-framework control mapping ✅ Session 2
- Auto-generated security policies — 10-template starter pack ✅ Session 4
- Evidence vault with cross-framework propagation ✅ Session 4
- Roadmap tracker auto-seeded from reports ✅ Session 4
- Continuous threat intelligence digest (Session 6)

## Build progress

| Session | Status | Scope |
|---------|--------|-------|
| 1 | ✅ | Backend foundation, multi-tenant auth, model schema |
| 2 | ✅ | Assessment engine, control library, framework mapping, scoring |
| 3 | ✅ | AI advisory engine — Claude RAG + structured report generation |
| 4 | ✅ | Policy templates, evidence vault, roadmap tracker |
| 5 | ✅ | Dashboard frontend |
| 6 | ✅ | Knowledge base seed: 101 controls, 87 mappings, 44 snippets across 6 frameworks |
| 7 | ✅ | Paystack billing, free tier, Railway / Vercel deploy config, marketing landing page |

## Stack

- **API**: FastAPI (Python 3.11+)
- **DB**: PostgreSQL with pgvector (sqlite for tests)
- **Cache/queue**: Redis
- **AI**: Claude API (claude-opus-4-7) via Anthropic SDK, with mock seam
- **Templating**: Jinja2 + YAML front-matter for policies
- **Auth**: JWT + refresh tokens, multi-tenant
- **Deploy target**: Railway

## Quickstart

```bash
pip install -r requirements.txt
cp .env.production.example .env
pytest                              # 244 tests should pass
python -m app.cli seed-info         # preview the seed corpus
python -m app.cli seed              # populate frameworks, controls, mappings
uvicorn app.main:app --reload
```

## Seed pipeline

The platform ships with a curated knowledge base under `app/data/`:

- `app/data/frameworks/*.yaml` — one file per compliance framework (SOC 2,
  NDPA, CBN cybersecurity framework, ISO 27001, POPIA, Kenya DPA). Each
  file declares the framework metadata and its controls.
- `app/data/mappings.yaml` — cross-framework control mappings with strength
  (`equivalent`, `partial`, `related`). This is what makes a single piece
  of evidence cover multiple frameworks.
- `app/data/knowledge/*.yaml` — paraphrased advisory text the AI advisor
  retrieves and grounds its reports in. Six files, ~44 snippets covering
  per-framework guidance and cross-cutting practical patterns.

Current totals: **6 frameworks, 101 controls, 87 cross-framework mappings,
44 knowledge snippets**.

The seed is **idempotent** — running `python -m app.cli seed` repeatedly
produces the same DB state. Production deploys should run it as a release
hook. Running it locally:

```bash
python -m app.cli seed-info  # show what would be loaded
python -m app.cli seed       # actually load
```

Adding a new framework or control is a YAML edit, not a code change. The
`FrameworkSeed` and `MappingSeed` Pydantic schemas validate every file at
seed time — typos and dangling references fail loud.

## Endpoints (v1)

```
GET    /api/v1/health
GET    /api/v1/ready

POST   /api/v1/auth/signup
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me

GET    /api/v1/questionnaires/latest
GET    /api/v1/questionnaires/{version}

POST   /api/v1/assessments
GET    /api/v1/assessments
GET    /api/v1/assessments/{id}
PATCH  /api/v1/assessments/{id}/responses
GET    /api/v1/assessments/{id}/progress
POST   /api/v1/assessments/{id}/submit          generates report + seeds roadmap

GET    /api/v1/reports
GET    /api/v1/reports/{id}
GET    /api/v1/reports/by-assessment/{id}

GET    /api/v1/policy-templates                 list 10 v1 templates
GET    /api/v1/policy-templates/{code}
POST   /api/v1/policies                         generate one policy as draft
POST   /api/v1/policies/starter-pack            generate the full set
GET    /api/v1/policies
GET    /api/v1/policies/{id}
POST   /api/v1/policies/{id}/publish            archives prior version
POST   /api/v1/policies/{id}/archive
POST   /api/v1/policies/{id}/acknowledge        idempotent per user
GET    /api/v1/policies/{id}/acknowledgments

POST   /api/v1/evidence                         submit; returns propagated coverage
GET    /api/v1/evidence
GET    /api/v1/evidence/{id}
PATCH  /api/v1/evidence/{id}/status
GET    /api/v1/evidence/by-control/{fw}/{code}  direct + propagated
GET    /api/v1/evidence/coverage/matrix         per-framework coverage

POST   /api/v1/roadmap/seed-from-report/{id}    idempotent seed
GET    /api/v1/roadmap/items                    filter by report_id, status
GET    /api/v1/roadmap/items/{id}
PATCH  /api/v1/roadmap/items/{id}               status, assignee, notes, due
GET    /api/v1/roadmap/progress

GET    /api/v1/billing/pricing                  pricing in company's currency
GET    /api/v1/billing/subscription             current subscription state
POST   /api/v1/billing/checkout                 start checkout, returns auth URL
POST   /api/v1/billing/cancel                   cancel current subscription
POST   /api/v1/billing/webhook                  Paystack webhook (HMAC-SHA512 signed)
```

## Billing — Paystack

Subscription billing is Paystack-backed with native pricing in NGN, KES, ZAR,
GHS, and USD. Currency is locked at signup based on the company's country and
never changes.

**Tiers:**
- **Free** — 1 assessment, 3 evidence items, 1 policy, NDPA + 1 framework, no AI advisor
- **Starter** — 4 assessments, 25 evidence, 5 policies, 2 frameworks, AI advisor (₦40K/mo)
- **Growth** — Unlimited assessments / evidence / policies / frameworks, AI advisor, priority support (₦100K/mo)
- **Audit-Ready** — Growth + dedicated reviewer + audit prep workshop (₦250K/mo)

Pricing for KES, ZAR, GHS, and USD is set at locally-appropriate price points,
not just FX-converted. Edit `app/services/billing/catalog.py` to adjust.

**Plan setup:** after deploying, run `python -m app.cli sync-plans` once. It
creates Paystack plans from the catalog and prints shell-format env vars to
add to your environment so the backend knows each tier's plan_code.

**Webhook signing:** all Paystack webhooks are verified with HMAC-SHA512 over
the raw body using `PAYSTACK_SECRET_KEY`. Failure is fail-closed (401).

**Tier limit enforcement:** when a free-tier user hits a cap, the API returns
HTTP 402 with a structured `tier_limit` detail the dashboard surfaces as an
upgrade prompt (rather than a generic error).

## Deployment

**Railway (backend):**
```bash
railway link
railway up
# After first deploy:
railway run python -m app.cli sync-plans  # capture plan codes
# Add the printed PAYSTACK_PLAN_* env vars in Railway dashboard
```

The `railway.toml` runs `alembic upgrade head` and `python -m app.cli seed`
on every release. Both are idempotent — the seed updates content but never
duplicates, and Alembic skips already-applied migrations.

**Vercel (dashboard + landing):** see the dashboard repo's README. The landing
site is a separate Vite project under `cybercapsec-landing/`.

## Architecture highlights

### Policies as Markdown with YAML front-matter

Every policy template is a `.md` file under `app/services/policies/templates/`.
Front-matter declares metadata (template_code, framework_codes, control_refs,
variables); body is a Jinja2 template. Adding a new policy: drop a file in,
register the code in `PolicyTemplateCode`, tests pick it up. v1 ships 10
templates: Information Security, Access Control, Data Protection, Data
Retention, Incident Response, Acceptable Use, Vendor Management, Change
Management, Backup & Recovery, Security Awareness Training.

### Rendered content is frozen

A `Policy` row stores rendered Markdown plus a snapshot of the variables
used. Templates can evolve (template_version goes up) without invalidating
existing rendered policies. Acknowledgments are tied to a specific Policy
version — auditable trail of who agreed to what.

### Evidence with cross-framework propagation

Evidence is anchored at one `(framework, control_code)` pair. Via the
`ControlMapping` table from Session 2, evidence implicitly satisfies mapped
controls in other frameworks. EQUIVALENT mappings propagate by default;
PARTIAL mappings are exposed but flagged. The `coverage/matrix` endpoint
returns per-framework satisfied controls including propagated ones — the
unit-economics win that makes "prep once, comply everywhere" real.

Five evidence kinds are supported: `external_link` (Notion / Google Docs /
GitHub PRs — what 80% of early SOC 2 prep actually looks like),
`policy_ref` (link to a Policy in our system), `screenshot_url`,
`narrative` (text-only description), and `file_upload` (reserved — returns
501 until S3-backed uploads ship).

### Roadmap items: mutable working surface, immutable report snapshot

Reports are immutable artifacts. RoadmapItems are mutable working tasks
seeded from a report's roadmap array. Seeding is idempotent (keyed by
`report_id + source_task_id`). Reports stay auditable; RoadmapItems carry
status, assignee, due date, notes, blocked reason, and completion timestamp.

Submission auto-seeds the roadmap so users can start tracking immediately.
Progress aggregation gives them a single completion percentage across all
items or a single report.

### Mock-first AI seam (continued from Session 3)

`USE_MOCK_AI=true` returns deterministic plausible reports without calling
Claude. Tests run free; the dashboard in Session 5 develops against
realistic data; the production seam to Claude is one config flag away.

### Multi-tenancy guardrail

`get_tenant_object_or_404` is the single chokepoint for tenant-scoped
reads. Cross-tenant access raises 404 (never 401, to avoid leaking
existence). Every new endpoint in Session 4 routes through it.

## License

Proprietary — CyberCapSec Ltd.
