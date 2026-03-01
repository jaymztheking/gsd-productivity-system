# File Glossary

Every file in the project, organized by component and function.

---

## Root

### Config

| File | Purpose |
|------|---------|
| `.env` | Active environment variables (ports, credentials, database URL). Git-ignored. |
| `.env.example` | Committed template of `.env` with safe defaults for new clones. |
| `.gitignore` | Excludes `__pycache__`, `node_modules`, `.env`, `dist`, OS files. |

### Orchestration

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Defines all 4 services (postgres, api, ui, n8n), named volumes, port mappings, health checks, and startup dependencies. |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Quick start, architecture overview, deployment guides (cloud Postgres, k3s, cross-arch builds, iOS Shortcut setup). |
| `DECISIONS.md` | Rationale behind non-obvious design choices. |
| `FILE-GLOSSARY.md` | This file. Per-file descriptions organized by component and function. |
| `LOG.md` | Chronological build log of what was done in each implementation phase. |

---

## API (`api/`)

### Config

| File | Purpose |
|------|---------|
| `Dockerfile` | Production image: `python:3.12-slim`, installs deps from `requirements.txt`, copies app code, runs uvicorn. |
| `.dockerignore` | Excludes `__pycache__`, `.env`, `.git` from Docker build context. |
| `pyproject.toml` | Project metadata and dependency declaration (used by pip for editable installs). |
| `requirements.txt` | Pinned dependency list for `pip install` inside Docker. Mirrors `pyproject.toml` deps. |
| `app/config.py` | Pydantic Settings class. Reads `DATABASE_URL` from env. Exposes `SYNC_DATABASE_URL` property that swaps `asyncpg` for `psycopg2` (needed by Alembic's synchronous migration runner). |

### Database / Migrations

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration. Sets script location, logging. The `sqlalchemy.url` is overridden programmatically by `env.py`. |
| `alembic/env.py` | Alembic's runtime entry point. Imports `Base.metadata` for schema discovery and `settings.SYNC_DATABASE_URL` for connection. Runs migrations synchronously via psycopg2. |
| `alembic/script.py.mako` | Template for auto-generated migration files (used by `alembic revision`). |
| `alembic/versions/001_create_tables.py` | Creates all 4 tables: `tags`, `projects`, `next_actions`, `next_action_tags`. Defines Postgres enum types (`action_status`, `project_status`, `tag_category`). Creates indexes on `status`, `project_id`, and junction table FKs. |
| `alembic/versions/002_seed_tags.py` | Inserts the 13 seed tags (4 context, 5 time, 4 energy) using deterministic UUIDs via `uuid5` for cross-environment consistency. |

### Models (ORM)

| File | Purpose |
|------|---------|
| `app/models/__init__.py` | Defines the SQLAlchemy `DeclarativeBase` class. Imports all models so Alembic can discover them. |
| `app/models/enums.py` | Python string enums: `ActionStatus` (inbox/active/pending/complete), `ProjectStatus` (active/complete), `TagCategory` (context/time/energy). Used by both ORM models and Pydantic schemas. |
| `app/models/tag.py` | `Tag` ORM model: `id` (UUID PK), `name` (unique text), `category` (enum). |
| `app/models/project.py` | `Project` ORM model: `id`, `name`, `status`, `index_notes`, timestamps. Has `next_actions` relationship. |
| `app/models/next_action.py` | `NextAction` ORM model: `id`, `title`, `notes`, `status`, `project_id` (FK), timestamps, `completed_at`. Defines the `next_action_tags` junction table. Has `tags` and `project` relationships with `selectin` eager loading. |

### Schemas (Pydantic)

| File | Purpose |
|------|---------|
| `app/schemas/__init__.py` | Empty package init. |
| `app/schemas/tag.py` | `TagOut` response schema. |
| `app/schemas/project.py` | `ProjectCreate`, `ProjectUpdate` request schemas. `ProjectOut` response schema. |
| `app/schemas/next_action.py` | `NextActionCreate`, `NextActionUpdate` request schemas. `NextActionOut` response schema (includes nested `TagOut` and `ProjectOut`). |

### CRUD (Database Queries)

| File | Purpose |
|------|---------|
| `app/crud/__init__.py` | Empty package init. |
| `app/crud/tags.py` | `list_tags()` — select all, ordered by category then name. |
| `app/crud/projects.py` | `list_projects()`, `get_project()`, `create_project()`, `update_project()`. |
| `app/crud/next_actions.py` | The most complex module. `list_next_actions()` implements AND-filter via `JOIN + GROUP BY + HAVING COUNT`. `create_next_action()` and `update_next_action()` handle tag association. `update_next_action()` manages `completed_at` timestamp on status transitions. |

### Routers (HTTP Endpoints)

| File | Purpose |
|------|---------|
| `app/routers/__init__.py` | Empty package init. |
| `app/routers/tags.py` | `GET /tags` — returns all tags for UI dropdowns/toggles. |
| `app/routers/projects.py` | `GET /projects`, `POST /projects` (201), `PATCH /projects/:id`. 404 on missing project. |
| `app/routers/next_actions.py` | `GET /next-actions` (with `status` and `tag_ids` query params), `POST /next-actions` (201), `PATCH /next-actions/:id`, `DELETE /next-actions/:id` (204). 404 on missing action. |

### Application Entry

| File | Purpose |
|------|---------|
| `app/__init__.py` | Empty package init. |
| `app/main.py` | FastAPI application factory. Configures CORS (allow all origins for single-user system). Mounts all three routers. Exposes `/health` endpoint. |
| `app/database.py` | Creates the async SQLAlchemy engine and session factory. Exposes `get_db()` async generator for FastAPI dependency injection. |

---

## UI (`ui/`)

### Config

| File | Purpose |
|------|---------|
| `Dockerfile` | Production multi-stage build: stage 1 (`node:20-alpine`) installs deps and builds; stage 2 (`nginx:alpine`) serves the static bundle. |
| `Dockerfile.dev` | Dev image: `node:20-alpine`, installs deps, runs `npm run dev` with Vite's HMR. |
| `.dockerignore` | Excludes `node_modules`, `dist`, `.git` from Docker build context. |
| `package.json` | Dependencies: React 19, React Router 7, Vite 6, TypeScript 5.7. Scripts: `dev`, `build`, `preview`. |
| `package-lock.json` | Lockfile for deterministic installs. |
| `tsconfig.json` | Root TypeScript config. References `tsconfig.app.json` and `tsconfig.node.json`. |
| `tsconfig.app.json` | TypeScript config for app source (`src/`). Targets ES2020, JSX react-jsx, strict mode. |
| `tsconfig.node.json` | TypeScript config for Vite config file. Targets ES2022. |
| `vite.config.ts` | Vite configuration. React plugin, dev server on port 3000, proxy `/api/*` to `http://api:8000/*` (strips `/api` prefix). |
| `nginx.conf` | Production Nginx config. Serves SPA with `try_files` fallback to `index.html`. Proxies `/api/` to the API container. Listens on port 3000. |

### Entry

| File | Purpose |
|------|---------|
| `index.html` | HTML shell. Sets viewport for mobile (`viewport-fit=cover`). Mounts the React app at `#root`. |
| `src/main.tsx` | React entry point. Renders `<App />` inside `StrictMode` into `#root`. |
| `src/App.tsx` | Route definitions using React Router. `/` redirects to `/engage`. Layout wraps both `/engage` and `/intake` routes. Imports global CSS. |

### Types

| File | Purpose |
|------|---------|
| `src/types/models.ts` | TypeScript interfaces matching the API's Pydantic response schemas: `Tag`, `Project`, `NextAction`, plus string literal types for `ActionStatus`, `ProjectStatus`, `TagCategory`. |

### API Client

| File | Purpose |
|------|---------|
| `src/api/client.ts` | Typed fetch wrapper for all API calls. Functions: `fetchTags`, `fetchProjects`, `createProject`, `updateProject`, `fetchNextActions` (builds repeated `tag_ids` query params), `createNextAction`, `updateNextAction`, `deleteNextAction`. Base path is `/api` (proxy handles rewrite). |

### Hooks (Data Layer)

| File | Purpose |
|------|---------|
| `src/hooks/useTags.ts` | Fetches all tags on mount. Returns `tags` array and `tagsByCategory` grouped record for easy rendering in selectors. |
| `src/hooks/useProjects.ts` | Fetches projects on mount. Exposes `createProject()` for inline project creation. |
| `src/hooks/useNextActions.ts` | Fetches next actions with optional `status` and `tag_ids` filters. Refetches when params change. Exposes `createAction`, `updateAction`, `deleteAction`, `removeFromList` for optimistic UI updates. |

### Shared Components

| File | Purpose |
|------|---------|
| `src/components/Layout.tsx` | App shell with sticky top nav. Two `NavLink` tabs (Engage, Intake) with active state styling. Renders child routes via `<Outlet />`. |
| `src/components/TagBadge.tsx` | Colored pill displaying a tag name. Color determined by category (blue=context, amber=time, green=energy) via CSS custom property. |
| `src/components/TagSelector.tsx` | Radio-style button group for selecting one tag per category. Tapping the active tag deselects it. Used in both Intake (triage) and Engage (filtering). |
| `src/components/ProjectSelector.tsx` | Dropdown for project assignment. Lists active projects, "None" option, and "+ New Project..." which expands inline fields for name and index notes. |

### Pages — Intake

| File | Purpose |
|------|---------|
| `src/pages/IntakePage.tsx` | Inbox processing queue. Fetches `status=inbox` items oldest-first. Displays one item at a time via `IntakeCard`. Shows remaining count. "Inbox Zero" empty state when done. |
| `src/pages/IntakeCard.tsx` | Single inbox item with three actions: **Ignore** (delete), **Make Task** (expand to edit title, notes, tags, project, then save as active), **Make Project** (expand to create project and remove inbox item). Expanded states are mutually exclusive. |

### Pages — Engage

| File | Purpose |
|------|---------|
| `src/pages/EngagePage.tsx` | The core product. Manages filter state (one tag per category + show-pending toggle). Fetches active actions (and optionally pending) filtered by selected tags. Handles optimistic completion (card removed immediately, rollback on API failure). |
| `src/pages/FilterPanel.tsx` | Three rows of tag toggle buttons (context, energy, time) plus a show-pending toggle switch. Selected buttons get filled background in their category color. All taps are large (44px+). |
| `src/pages/TaskCard.tsx` | Individual task row. Collapsed: title, tag badges, project name, notes preview, completion circle button. Pending items have amber left border and "Pending" label. Expanded (on tap): full edit form with title, notes, tag selectors, project selector, status toggle. Completion animates the card off-screen. |

### Styles

| File | Purpose |
|------|---------|
| `src/styles/index.css` | Global styles. CSS custom properties for dark theme colors, spacing, radii, 44px tap targets. Mobile-first responsive layout. Components: nav bar, buttons (primary/danger/success/ghost), form inputs, tag badges, tag selector buttons, toggle switch, cards (with pending and exit animation variants), empty states, utility classes. Uses `dvh`, `env(safe-area-inset-*)`, and `color-mix()` for modern mobile support. |

---

## n8n (`n8n/`)

### Workflows

| File | Purpose |
|------|---------|
| `workflows/inbox-capture.json` | n8n workflow definition. Webhook node (POST `/capture`) receives `{ "title": "..." }` and HTTP Request node forwards it to `POST http://api:8000/next-actions` with `status: "inbox"`. Import into n8n UI to activate. |
| `workflows/weekly-digest.json` | n8n workflow definition. Schedule trigger (Sunday 7pm) fires 4 parallel HTTP requests to the API (inbox, active, pending, projects). Code node compiles an HTML digest covering unprocessed inbox items, stale actions (7+ days untouched), pending items, someday items, and projects without next actions. Email Send node delivers via SMTP. |
