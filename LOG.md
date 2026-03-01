# Build Log

Chronological record of what was done in each implementation phase.

---

## Phase 1: Foundation

- Created project directory structure (`api/`, `ui/`, `n8n/`)
- Wrote `.env`, `.env.example`, `.gitignore`
- Wrote `docker-compose.yml` with 4 services: `postgres` (15-alpine, named volume, health check), `api` (FastAPI), `ui` (Vite dev server), `n8n` (official image)
- Built API Dockerfile with `requirements.txt` for dependency installation
- Wrote `app/config.py` (Pydantic Settings with `DATABASE_URL` and sync URL property for Alembic)
- Wrote `app/database.py` (async SQLAlchemy engine, session factory, `get_db` dependency)
- Defined all ORM models: `Tag`, `Project`, `NextAction`, `next_action_tags` junction table
- Defined Python enums: `ActionStatus`, `ProjectStatus`, `TagCategory`
- Configured Alembic (`alembic.ini`, `env.py`, `script.py.mako`)
- Wrote migration `001_create_tables.py`: creates all 4 tables with Postgres enum types, foreign keys, and indexes
- Wrote migration `002_seed_tags.py`: inserts 13 seed tags with deterministic UUIDs
- Wrote minimal `app/main.py` with `/health` endpoint and CORS middleware
- **Issue encountered**: `ModuleNotFoundError: No module named 'app'` in Alembic. Fixed by adding `PYTHONPATH=/app` to the API container environment
- **Issue encountered**: Port 5432 already allocated. Changed host-mapped Postgres port to 5433
- Verified: Postgres healthy, migrations run, `/health` returns 200, `SELECT * FROM tags` shows 13 rows

## Phase 2: API Endpoints

- Wrote Pydantic schemas: `TagOut`, `ProjectCreate/Update/Out`, `NextActionCreate/Update/Out`
- Wrote CRUD layer: `tags.py` (list all), `projects.py` (list/get/create/update), `next_actions.py` (list with AND-filter, get, create, update with tag replacement, delete)
- Implemented AND-filter logic: `JOIN next_action_tags WHERE tag_id IN (...) GROUP BY id HAVING COUNT = len(tag_ids)`
- Implemented status transition side effects: setting `completed_at` on transition to complete, clearing it on transition away
- Wrote routers: `tags.py` (GET /tags), `projects.py` (GET/POST/PATCH), `next_actions.py` (GET/POST/PATCH/DELETE)
- `tag_ids` filter accepts repeated query params: `?tag_ids=uuid1&tag_ids=uuid2`
- Mounted all routers in `main.py`
- **Issue encountered**: timezone mismatch with asyncpg (`can't subtract offset-naive and offset-aware datetimes`). Fixed by using `datetime.utcnow()` (naive) instead of `datetime.now(timezone.utc)` to match `TIMESTAMP WITHOUT TIME ZONE` columns
- Verified: all endpoints work via `/docs`, AND-filter returns correct results, delete returns 204, completion sets `completed_at`

## Phase 3: Frontend Scaffold

- Initialized UI with `package.json` (React 19, React Router 7, Vite 6, TypeScript 5.7)
- Wrote `vite.config.ts` with dev proxy: `/api/*` rewrites to `http://api:8000/*`
- Wrote TypeScript configs (`tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`)
- Wrote `Dockerfile.dev` (dev with volume mount + HMR) and `Dockerfile` (multi-stage prod build with Nginx)
- Wrote `nginx.conf` for production: SPA fallback + API proxy
- Wrote `src/types/models.ts` matching all API response schemas
- Wrote `src/api/client.ts`: typed fetch wrapper with functions for all endpoints
- Wrote hooks: `useTags` (with `tagsByCategory` grouping), `useProjects` (with inline create), `useNextActions` (with filter params, refetch on change, optimistic mutations)
- Wrote shared components: `Layout` (nav with active tab styling), `TagBadge` (colored pill), `TagSelector` (radio-style toggle buttons per category), `ProjectSelector` (dropdown with inline new project creation)
- Wrote `src/styles/index.css`: dark theme, mobile-first, 44px tap targets, CSS custom properties, `dvh`/`safe-area-inset` support
- Set up routing in `App.tsx`: `/` redirects to `/engage`, Layout wraps both routes
- Verified: UI container serves at port 3000, API proxy works (`/api/tags` returns data)

## Phase 4: Intake UI

- Wrote `IntakePage.tsx`: queue-style inbox processor, fetches `status=inbox` oldest-first, shows one item at a time with remaining count, "Inbox Zero" empty state
- Wrote `IntakeCard.tsx`: three actions (Ignore/Make Task/Make Project) with expandable forms, mutually exclusive expanded states, tag selectors and project selector inline
- Make Task flow: edit title, add notes, select one tag per category, assign project, save as active
- Make Project flow: enter project name and index notes, creates project and removes inbox item
- Seeded 3 inbox items for testing

## Phase 5: Engage UI

- Wrote `FilterPanel.tsx`: three rows of tag toggle buttons (context, energy, time) with category-colored selection state, plus show-pending toggle switch
- Wrote `TaskCard.tsx`: collapsed view (title, tags, project, notes preview, completion circle), expanded edit view (full form with all fields), pending items get amber border + label, completion animates card off-screen
- Wrote `EngagePage.tsx`: manages filter state as `Record<TagCategory, string | null>`, collects active tag IDs for API query, fetches both active and pending when toggle is on (two parallel API calls merged), optimistic completion with rollback on failure
- Seeded active and pending test items with various tag combinations
- Verified: filter toggles narrow the list, AND logic works, inline edit saves, completion removes cards

## Phase 6: n8n Workflows

- Wrote `inbox-capture.json`: Webhook node (POST `/capture`) receives `{ "title" }` and HTTP Request node creates inbox item via API
- Wrote `weekly-digest.json`: Schedule trigger (Sunday 7pm), 4 parallel HTTP requests to API (inbox/active/pending/projects), Code node compiles HTML digest (inbox count, stale actions 7+ days, pending items, someday items, projects without next actions), Email Send node delivers via SMTP
- Workflows are importable JSON files for the n8n UI

## Phase 7: Polish & Documentation

- Added `.dockerignore` files for both `api/` and `ui/` to reduce Docker build context
- Wrote `README.md`: architecture diagram, quick start, port table, cloud Postgres swap instructions, cross-arch build instructions, k3s deployment guide, iOS Shortcut setup, API endpoint reference, tag taxonomy, data model summary
- Wrote `DECISIONS.md`: rationale for FastAPI over Express, React over Svelte, single UI container, no state management library, stock Postgres image, hand-written migrations, deterministic UUIDs, naive timestamps, tags as first-class data, someday as tag not status, API proxy pattern, mobile-first design choices
- Wrote `FILE-GLOSSARY.md`: every file described, organized by component (root, API, UI, n8n) and function (config, migration, model, schema, CRUD, router, entry, types, client, hooks, components, pages, styles, workflows)
- Wrote `LOG.md`: this file
