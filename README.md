# GSD (Getting Shit Done)

Personal GTD-inspired productivity system. Capture tasks from anywhere, triage them in an inbox, then filter by your current context to find what to do right now.

## Architecture

```
iOS Reminders ──> n8n webhook ──> API ──> Postgres
                                  ↑
                              UI (React)
                         /intake    /engage
```

- **Postgres 15** — single source of truth
- **FastAPI** — async REST API, all CRUD + tag-based AND-filtering
- **React + Vite** — single app serving Intake (triage) and Engage (filter + do) routes
- **n8n** — capture webhook + weekly review digest

## Quick Start (Local Dev)

```bash
# Clone and start
git clone <repo-url> && cd gsd-productivity-system
cp .env.example .env  # Edit as needed (ports, credentials)
docker compose up --build -d

# Verify
curl http://localhost:8000/health        # API
curl http://localhost:8000/tags          # Seed tags
open http://localhost:3000               # UI (redirects to /engage)
open http://localhost:3000/intake        # Intake UI
open http://localhost:5678               # n8n (admin/admin)
```

Default ports (configurable via `.env`):
| Service  | Port |
|----------|------|
| Postgres | 5433 (host) → 5432 (container) |
| API      | 8000 |
| UI       | 3000 |
| n8n      | 5678 |

## Swapping Postgres to Cloud

Change one environment variable:

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@your-cloud-host:5432/gsd
```

Remove or stop the `postgres` service from docker-compose.yml. Everything else stays the same. The API runs Alembic migrations on startup, so tables will be created in the new database automatically.

## Cross-Architecture Builds (for Raspberry Pi k3s)

All base images support both `linux/amd64` and `linux/arm64`. To build ARM64 images from an x86 dev machine:

```bash
# One-time setup
docker buildx create --name multiarch --use

# Build API for ARM64
docker buildx build --platform linux/arm64 -t gsd-api:latest ./api --load

# Build UI for ARM64
docker buildx build --platform linux/arm64 -t gsd-ui:latest ./ui --load
```

Or build natively on the Pi — just `docker compose up --build`.

## k3s Deployment

The same container images run on k3s. Create Kubernetes manifests (Deployment + Service for each) pointing to the same images. Key config:

- Set `DATABASE_URL` via a Kubernetes Secret
- Use a PersistentVolumeClaim for Postgres data (or point at managed cloud Postgres)
- Expose the UI via an Ingress or NodePort

## iOS Shortcut Setup

1. Open the Shortcuts app on your iPhone
2. Create a new Shortcut triggered by "When I add a Reminder to [GSD Inbox] list"
3. Add action: "Get Contents of URL"
   - URL: `http://<your-n8n-host>:5678/webhook/capture`
   - Method: POST
   - Request Body: JSON — `{ "title": "Shortcut Input" }` (use the Reminder title variable)
4. Now Siri, CarPlay, and manual Reminders entries all feed into GSD

Alternatively, send captures directly to the API:
```bash
curl -X POST http://localhost:8000/next-actions \
  -H "Content-Type: application/json" \
  -d '{"title": "Your task here"}'
```

## n8n Workflows

Import the workflow JSON files from `n8n/workflows/` into your n8n instance:

1. **Inbox Capture** (`inbox-capture.json`) — Webhook receives `{ "title": "..." }` and creates an inbox item
2. **Weekly Digest** (`weekly-digest.json`) — Runs Sunday 7pm, queries the API for inbox items, stale actions, pending items, and projects missing next actions, then emails a formatted digest

To import: n8n UI → Workflows → Import from File.

## API Endpoints

```
GET    /tags                    — all tags (seed data, 13 tags)
GET    /projects                — list projects
POST   /projects                — create project
PATCH  /projects/:id            — update project

GET    /next-actions            — list (filter: ?status=active&tag_ids=uuid1&tag_ids=uuid2)
POST   /next-actions            — create
PATCH  /next-actions/:id        — update
DELETE /next-actions/:id        — delete
```

Tag filtering uses AND logic: `?tag_ids=a&tag_ids=b` returns only actions tagged with **both** a and b.

Auto-generated API docs: `http://localhost:8000/docs`

## Tag Taxonomy

| Category | Tags |
|----------|------|
| Context  | @home, @online, @errands, @calls |
| Time     | #now, #today, #week, #month, #someday |
| Energy   | +easy, +routine, +focused, +peak |

## Data Model

- **next_actions** — the atomic unit. Status: inbox → active/pending → complete
- **tags** — first-class entities (not text parsing). Joined via `next_action_tags`
- **projects** — container for related actions. Status: active → complete
