# Design Decisions

Rationale behind the non-obvious choices in GSD's architecture and implementation.

---

## Language & Framework

**API: FastAPI (Python) over Node/Express**

- User requirement was best performance above all else
- FastAPI on uvicorn + asyncpg is one of the fastest Python stacks available, competitive with Go for I/O-bound CRUD workloads
- Auto-generated OpenAPI docs (`/docs`) eliminate the need for separate API documentation
- Pydantic gives request/response validation for free

**Frontend: React + Vite (TypeScript) over Svelte or vanilla**

- User wants future portability to a native iOS app
- React shares paradigm and component model with React Native, making migration straightforward
- Vite provides fast HMR in dev and optimized builds for production

## Single UI Container, Two Routes

The spec called for separate `intake-ui` and `engage-ui` containers. We merged them into a single React app with `/intake` and `/engage` routes because:

- Shared components (TagSelector, TagBadge, ProjectSelector) would be duplicated across two apps
- One container is simpler to deploy, build, and maintain
- Both UIs share the same API client and type definitions
- The user confirmed this approach during planning

## No State Management Library

React's built-in `useState` + custom hooks handle all data needs. No Redux, Zustand, or similar:

- The app has exactly two pages with independent data requirements
- Each page fetches its own data and manages its own state
- No cross-page state sharing is needed (Engage and Intake are independent workflows)
- Adding a state library would be premature complexity at this scale

## Database

**Stock Postgres image, no custom Dockerfile**

- The Postgres container uses `postgres:15-alpine` directly with zero customization
- Schema is defined entirely in Alembic migration files inside `api/alembic/versions/`
- This makes Postgres trivially swappable: change `DATABASE_URL` to point at Supabase, Neon, or RDS, remove the Postgres container, done
- A `db/` folder with init scripts would add coupling that works against this portability goal

**Hand-written migrations over Alembic autogenerate**

- Autogenerate struggles with Postgres enum types, junction tables, and seed data
- Hand-written migrations are explicit, reviewable, and predictable
- For a schema this small (4 tables), the overhead is minimal

**Deterministic UUIDs for seed tags (`uuid5`)**

- Seed tags get the same UUID across every environment (dev, staging, prod)
- Makes it safe to reference tag IDs in n8n workflows, test data, or future automations
- The fixed namespace UUID `d1b0e1a2-3c4d-5e6f-7a8b-9c0d1e2f3a4b` is arbitrary but stable

**Naive UTC timestamps (no timezone info)**

- All `DateTime` columns use `TIMESTAMP WITHOUT TIME ZONE`
- Python code uses `datetime.utcnow()` (naive) to match
- asyncpg throws errors when mixing timezone-aware and naive datetimes
- For a single-user system in one timezone, this is sufficient. If multi-tz support were needed, switch to `TIMESTAMP WITH TIME ZONE`

## Tags as First-Class Data

Tags are rows in a `tags` table joined via `next_action_tags`, not comma-separated text on the action:

- Filtering is SQL joins + `HAVING COUNT`, not `LIKE` queries or text parsing
- AND-filter logic: `WHERE tag_id IN (...) GROUP BY id HAVING COUNT = N` ensures the action has all requested tags
- Tag taxonomy is enforced by the database (categories are a Postgres enum)
- Adding new tags later is an Alembic migration, not a code change

## `#someday` Is a Tag, Not a Status

The spec explicitly calls this out: someday items are active next actions tagged `#someday`. There is no separate "someday" status because:

- It keeps the status enum minimal (inbox, active, pending, complete)
- Someday items still appear in the Engage UI when you filter by `#someday`
- They participate in the weekly digest review
- If something will never happen, delete it rather than giving it a special status

## Pending Status vs. `@waiting` Tag

The spec uses `pending` status instead of a `@waiting` context tag:

- Status controls visibility in the Engage UI (the "Show Pending" toggle)
- A waiting context tag would compete with the actual context tags (@home, @online, etc.)
- Pending items are visually distinct (amber border) without occupying a filter slot

## API Proxy Through Vite/Nginx

The frontend calls `/api/...` and the proxy rewrites to the API container:

- Avoids CORS entirely in production (same origin)
- Frontend code never needs to know the API's actual hostname or port
- Vite handles the proxy in dev, Nginx handles it in production
- If auth is added later, cookies work naturally on same origin

## Docker Compose for Dev, k3s for Prod

- Docker Compose is the local dev workflow: `docker compose up` and everything works
- The same Dockerfiles and images run on k3s, just orchestrated differently
- k3s manifests are a stretch goal, not a v1 requirement
- All config is via environment variables, so switching orchestrators means changing env injection only

## Multi-Architecture Support

- Dev machines are x86_64 (Windows + macOS), production is ARM64 (Raspberry Pi 4)
- All base images (`python:3.12-slim`, `node:20-alpine`, `postgres:15-alpine`, `nginx:alpine`, `n8nio/n8n`) are multi-arch
- Custom Dockerfiles install only pure Python/Node packages with no arch-specific native binaries
- `docker buildx` enables cross-compilation from x86 to ARM64 without needing to build on the Pi

## Engage UI is the Default Route

`/` redirects to `/engage`, not `/intake`:

- The spec says "the engage UI is the product"
- You open the app when you want to find something to do, not when you want to triage
- Intake is a periodic processing task; Engage is the moment-to-moment interface

## Mobile-First Design Choices

- All interactive elements have a minimum 44px tap target (Apple's HIG recommendation)
- CSS uses `dvh` (dynamic viewport height) to handle iOS Safari's collapsing address bar
- `env(safe-area-inset-*)` handles iPhone notch and home bar
- Dark theme by default (easier on eyes, looks native on iPhone)
- Filter buttons are large, spaced, and one-thumb reachable
- Completion button is a circle on the right side of each card (natural thumb position for right-handed use)
