# CyberCapSec Advisory — Dashboard

React + Vite + TypeScript + Tailwind frontend for the CyberCapSec Advisory
platform. Talks to `cybercapsec-advisory-api`.

## Stack

- **Framework**: React 18 + Vite
- **Routing**: React Router v6
- **Server state**: TanStack Query
- **Styling**: Tailwind CSS (no UI library — utility classes + small inline components)
- **HTTP**: axios with auth interceptor + automatic token refresh
- **Markdown**: react-markdown for policy rendering
- **Tests**: Vitest + Testing Library + jsdom
- **Deploy target**: Vercel

## Build progress

| Session | Status | Scope |
|---------|--------|-------|
| 1 | ✅ | Backend foundation |
| 2 | ✅ | Assessment engine |
| 3 | ✅ | AI advisory engine |
| 4 | ✅ | Policies + evidence + roadmap |
| 5 | ✅ | Dashboard frontend (this) |
| 6 | ⏳ | Knowledge base seed expansion |
| 7 | ⏳ | Billing, deployment, landing page |

## Quickstart

```bash
npm install
cp .env.example .env  # set VITE_API_URL=http://localhost:8000
npm run dev           # http://localhost:5173

npm run typecheck
npm test              # 30 tests should pass
npm run build         # production build to dist/
```

## Pages

| Route | Page |
|-------|------|
| `/login` | Sign in |
| `/signup` | Create account + company |
| `/dashboard` | Posture summary, scores, top risks, roadmap progress |
| `/assessment` | Multi-step questionnaire form, autosave per section |
| `/roadmap` | Kanban view with click-to-edit task detail |
| `/policies` | List of generated policies grouped by status |
| `/policies/:id` | Rendered policy with publish/archive/acknowledge actions |
| `/evidence` | Submit evidence, see cross-framework propagation, view coverage matrix |
| `/reports` | List of AI-generated reports |
| `/reports/:id` | Full report: executive summary, framework gaps, risk register, roadmap snapshot |

## Architecture

### Auth flow

`AuthContext` owns the user state. On mount, if tokens are in `localStorage`,
it calls `/auth/me` to hydrate. On 401 from any API call, the axios
interceptor attempts a refresh; on success the original request is retried;
on failure the user is redirected to `/login`. Concurrent 401s during a
single refresh are queued so we make at most one refresh request.

### Server state

Every API call goes through TanStack Query via the hooks in `src/hooks`.
Query keys are centralized in `src/lib/queryKeys.ts` so invalidation is
predictable. Mutations invalidate their parent collections; the assessment
submit mutation invalidates everything that could have changed (reports,
roadmap, assessments).

### Type safety end-to-end

`src/types/api.ts` mirrors the backend Pydantic schemas. When the API
contract changes, TypeScript breaks compile. No runtime adapters or zod
schemas — we trust the backend's strict response validation.

### Why no shadcn/ui or component library

Inline Tailwind components in `src/components/UI.tsx` give us:

- Smaller bundle (141 KB gzipped including React)
- Full control over styling for the African startup brand
- No dependency on a UI library's release cadence

The components are simple enough to maintain inline.

## Deployment

```bash
# Set VITE_API_URL to your production backend
vercel
```

The included `vercel.json` configures:

- SPA rewrite (every path serves index.html so client-side routing works)
- Long-cache headers on hashed assets

## Connecting to the backend

The dashboard expects `cybercapsec-advisory-api` at `VITE_API_URL`. For local
development:

```
# Terminal 1
cd cybercapsec-advisory-api
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd cybercapsec-advisory-dashboard
npm run dev
```

CORS is configured on the backend to allow `http://localhost:5173` by default.

## License

Proprietary — CyberCapSec Ltd.
