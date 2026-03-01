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

## Capture: iOS Shortcut → n8n Webhook (MVP)

The capture pipeline is: "Hey Siri, capture task" → iOS Shortcut → POST to n8n webhook → API → Postgres inbox.

This was chosen over polling iCloud Reminders via CalDAV because:

- Simpler to implement — no iCloud app-specific passwords or CalDAV parsing
- Instant capture with zero delay (vs. 2–5 min polling interval)
- n8n webhook already exists and works

**Known tradeoffs (accepted for MVP):**

- Requires "capture task" phrasing, not natural "remind me to..." invocation
- No offline queue — fails silently if the server is unreachable (Reminders would queue offline and sync later)
- Phone must be on the same network as the server (until deployed to k3s with a real hostname/DNS)

**Future: Native iOS App**

A native iOS app is planned as a post-MVP iteration. It would replace the Shortcut entirely and enable:

- Background sync with offline queue (captures stored locally, pushed when online)
- Push notifications for pending item follow-ups and weekly review reminders
- Native Reminders integration via EventKit (monitor a Reminders list directly, no CalDAV polling)
- Siri Intents / App Intents for natural "remind me to..." capture that routes to GSD instead of Reminders
- Widgets for quick capture and at-a-glance active task counts
- Full Engage UI as a native view with proper iOS gestures (swipe to complete, haptic feedback)

The React frontend was chosen specifically to ease this transition — React → React Native shares paradigm and component logic.

## Mobile-First Design Choices

- All interactive elements have a minimum 44px tap target (Apple's HIG recommendation)
- CSS uses `dvh` (dynamic viewport height) to handle iOS Safari's collapsing address bar
- `env(safe-area-inset-*)` handles iPhone notch and home bar
- Dark theme by default (easier on eyes, looks native on iPhone)
- Filter buttons are large, spaced, and one-thumb reachable
- Completion button is a circle on the right side of each card (natural thumb position for right-handed use)

## Tag Ordering

Time and energy tags are ordinal data (#now < #today < #week < #month < #someday, +easy < +routine < +focused < +peak). A `sort_order` integer column on the `tags` table enforces display order everywhere — filter panels, tag selectors, API responses. Context tags are alphabetical.

## Project Hierarchy (Max 2 Levels)

Projects support a single level of nesting: root projects can have sub-projects, but sub-projects cannot have children. This is enforced at the API validation layer, not the database.

Sub-projects are **status-less task containers** — they group related tasks but don't carry their own active/complete status. Their purpose is to organize and optionally collapse tasks when a workstream is blocked (e.g., "Materials" sub-project under "Build a Deck" while waiting on delivery).

On project delete: sub-projects are re-parented to root (`parent_id = NULL`), tasks become unassigned (`project_id = NULL` via `SET NULL` FK).

## Soft Delete for Task History

Tasks use soft delete (`deleted_at` timestamp) instead of hard delete. This preserves a complete history of all tasks that passed through a project — both completed and removed. The project detail page shows this as a collapsible "Task History" log with visual distinction (green checkmark for completed, muted X for deleted).

This supports the GTD principle of reviewing what was accomplished while keeping the active task list clean.

## Task Reordering: Buttons over Drag-and-Drop

Project task lists use move-up/move-down chevron buttons instead of drag-and-drop because:

- Drag-and-drop conflicts with mobile scroll behavior
- No additional npm dependencies needed
- Chevron buttons fit the existing 44px tap target pattern
- Server-side ordering is a simple array of IDs (`PUT /projects/:id/tasks/order`)

## Inline Capture on Intake Page

The Intake page has a persistent "Capture" input at the top, even when the inbox is empty. This provides a quick way to add thoughts directly in the app without going through the iOS Shortcut pipeline. Useful for desktop usage and testing.
