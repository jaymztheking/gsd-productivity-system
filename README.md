# GSD (Getting Shit Done)

Personal GTD-inspired productivity system. Capture tasks from anywhere (Siri, Apple Watch, CarPlay, or directly in the app), triage them in an inbox, then filter by your current context to find what to do right now.

## Architecture

```
Siri / Apple Watch ──> iOS Shortcut ──> n8n webhook ──> API ──> Postgres
                                                         ↑
                                                     UI (React)
                                              /engage  /intake  /projects
```

- **Postgres 15** — single source of truth
- **FastAPI** — async REST API, full CRUD + tag-based AND-filtering
- **React + Vite** — single app serving Engage (filter + do), Intake (triage), and Projects (manage) routes
- **n8n** — capture webhook + weekly review digest

## Quick Start (Local Dev)

```bash
# Clone and start
git clone <repo-url> && cd gsd-productivity-system
cp .env.example .env  # Edit as needed (ports, credentials)

# Generate the shared API token and set it in .env
openssl rand -hex 32
# Paste it into API_TOKEN in .env

docker compose up --build -d

# Verify
curl http://localhost:8000/health        # API — open, no token needed
curl http://localhost:8000/tags          # 401: data endpoints require the token
curl -H "X-API-Token: $API_TOKEN" http://localhost:8000/tags   # Seed tags
open http://localhost:3000               # UI (redirects to /engage)
open http://localhost:3000/intake        # Intake UI
open http://localhost:3000/projects      # Projects UI
open http://localhost:5678               # n8n (admin/admin)
```

Default ports (configurable via `.env`):
| Service  | Port |
|----------|------|
| Postgres | 5433 (host) → 5432 (container) |
| API      | 8000 |
| UI       | 3000 |
| n8n      | 5678 |

## API Authentication

Every endpoint that reads or writes data requires a shared secret in the
`X-API-Token` header. `/health` is deliberately exempt so Kubernetes probes keep
working; it returns nothing but `{"status": "ok"}`.

A header was chosen over an interactive login because the primary client is an
iOS Shortcut, which can set arbitrary headers but cannot complete a login form.
The token is compared with `secrets.compare_digest`, and a missing token is
indistinguishable from a wrong one so the response reveals nothing.

`API_TOKEN` has no default. The API fails to start if it is unset, rather than
silently coming up unprotected.

### The browser never receives the token

The UI calls the API as same-origin relative paths (`/api/*`), and the proxy in
front of it attaches the token server-side — `ui/nginx.conf.template` in
production, `ui/vite.config.ts` in development. No frontend code holds the
secret, because anything shipped to the browser is readable by whoever loads the
page. Cloudflare Access authenticates the person; it does not hide the
JavaScript.

```
browser ──/api/*──> nginx ──X-API-Token: ···──> api:8000
                  (secret injected here, from env)
```

Because nothing is cross-origin, `CORS_ALLOW_ORIGINS` is normally empty. Set it
only if some other browser origin must call the API directly.

### Where the token lives

| Component | Source | Notes |
|---|---|---|
| API | `API_TOKEN` env | From `gsd-secrets` in k3s |
| UI proxy | `API_TOKEN` env | Rendered into nginx config by envsubst at startup |
| n8n workflows | `GSD API Token` credential | Header Auth, stored in n8n — see n8n Credentials below |
| iOS Shortcut | Shortcut definition | Stored in the iCloud keychain |

Local values live in `.env`; cluster values live in `k8s/secrets.yaml`. Both are
gitignored. Only placeholders are ever committed.

### n8n Credentials

n8n holds two secrets, and both live in n8n's credential store rather than in
environment variables or in the workflow files. That is not a stylistic choice:
n8n blocks `$env` access inside expressions by default
(`N8N_BLOCK_ENV_ACCESS_IN_NODE`), so a header built from `{{ $env.X }}` fails at
runtime with `access to env vars denied`. Credentials are referenced by name from
the exported JSON, so the workflows stay safe to commit.

Create both under **Credentials → Header Auth**:

| Credential name | Header name | Value | Guards |
|---|---|---|---|
| `GSD Capture Webhook Token` | `X-Webhook-Token` | its own secret | n8n's public webhook |
| `GSD API Token` | `X-API-Token` | same as `API_TOKEN` | the API behind it |

Keep these two values **different**. They protect different hops — the first stops
anonymous writes to the publicly reachable webhook, the second stops anonymous
calls to the API — so sharing one value means a single leak defeats both layers.

`GSD Capture Webhook Token` is attached to the Webhook node in
`inbox-capture.json`. `GSD API Token` is attached to every HTTP Request node in
both workflows: one in `inbox-capture.json`, four in `weekly-digest.json`.

After importing a workflow, confirm the credential is still linked on each node.
Imports reference credentials by name and sometimes drop the link.

### Rotating the token

The token is shared, so every holder must change together or captures start
failing. Rotate in this order:

```bash
NEW=$(openssl rand -hex 32)
```

1. **k3s** — update `API_TOKEN` in `k8s/secrets.yaml`, apply it, then restart
   both deployments so they pick it up:
   `kubectl -n gsd rollout restart deploy/api deploy/ui`
2. **n8n** — update the value on the `GSD API Token` credential. All five HTTP
   Request nodes across the two workflows use it, so nothing else in n8n changes
   and neither workflow JSON needs editing.
3. **iOS Shortcut** — update the `X-API-Token` header value in the Capture
   shortcut on one device; iCloud syncs it to Watch and CarPlay.
4. **Local dev** — update `API_TOKEN` in `.env`, then `docker compose up -d` to
   recreate the containers.

Verify afterwards that a capture from the Shortcut still lands in the inbox, and
that the UI still loads data. Rotating the webhook secret is a separate
operation: change it in the n8n credential and in the Shortcut's header.

## Running Tests

```bash
pip install -r api/requirements.txt          # includes pytest and httpx
PYTHONPATH=api pytest api/tests/test_auth.py -v
```

`test_auth.py` needs no database or running services — it stubs the session and
the crud calls to exercise the auth layer alone. `test_digest_pipeline.py` is an
integration suite and does need a live API:

```bash
API_URL=http://localhost:8000 PYTHONPATH=api pytest api/tests/test_digest_pipeline.py -v
```

## Remote Access (Cloudflare Tunnel)

GSD is reachable from anywhere without a port open on the router. `cloudflared`
runs in-cluster and dials *outbound* to Cloudflare, holding the connection open;
public requests arrive at Cloudflare and ride back down that established
connection. Nothing listens on the router, and clients speak ordinary HTTPS, so
no VPN profile or app is needed on any device — which is what makes Apple Watch
capture possible, since watchOS has no VPN client.

```
                          ┌─ Cloudflare Access (SSO) ─┐
browser ──https──> gsd.medaughsolutions.com ──────────┴──> ui:3000 ──> api:8000
                                                                 (nginx adds token)

Shortcut ─https─> capture.medaughsolutions.com/webhook/capture ──> n8n:80 ──> api:8000
                          (header secret, no SSO)
```

### Two hostnames, on purpose

| Hostname | Origin | Protected by |
|---|---|---|
| `gsd.medaughsolutions.com` | `ui.gsd.svc.cluster.local:3000` | Cloudflare Access SSO |
| `capture.medaughsolutions.com` | `n8n.n8n.svc.cluster.local:80`, path `/webhook/capture` only | `X-Webhook-Token` header |

Access policies attach per hostname. Keeping capture on its own hostname means
the SSO policy cannot end up in front of the Shortcut, which is unable to
complete an interactive challenge and would fail with a generic server error. A
path-bypass rule on a single shared hostname would also work, but is one careless
edit away from silently breaking capture.

The capture hostname is restricted to `^/webhook/capture/?$`. Everything else on
it — the n8n editor, other webhooks — is answered 404 by cloudflared and never
reaches the cluster.

**The tunnel points at the `ui` service, never at `api` directly.** The API
requires a token the browser cannot hold, so the UI's nginx attaches it in
transit. A Traefik ingress that routed `/api` straight to the API bypassed that
injection and had to be deleted; a tunnel aimed at the API would reproduce the
same failure.

### A consequence worth understanding

Because nginx attaches the API token in transit, **anything that can reach the UI
host can use the API without presenting a token.** On the LAN that means anyone
on your network; publicly it means anyone who passes Cloudflare Access. That is
inherent to a browser app that cannot hold a secret — Access is the thing
standing between the internet and your data, not the API token.

### Configuration

Manifests live in `k8s/cloudflared/`. Routing is in `configmap.yaml` rather than
configured by clicking in the dashboard, so it is reviewable and version
controlled. This is why the two public hostnames are plain **proxied CNAME
records** in Cloudflare DNS pointing at `<tunnel-id>.cfargotunnel.com`, rather
than entries added through the tunnel's "Public Hostname" tab — the latter writes
routing into Cloudflare's side, which then overrides the local config.

Two replicas spread across nodes, so a single node reboot does not drop the
tunnel. Verified by deleting one connector pod: requests continued uninterrupted
and Kubernetes scheduled a replacement on another node.

```bash
# Deploy (after creating the token Secret — see k8s/cloudflared/secret.yaml.example)
kubectl apply -f k8s/cloudflared/

# Health
kubectl -n cloudflared get pods
kubectl -n cloudflared logs deploy/cloudflared --tail=20
```

### Rotating the tunnel token

Tunnel credentials are separate from the API and webhook secrets. To rotate,
create a new tunnel in the dashboard (or refresh the connector token), then:

```bash
kubectl -n cloudflared delete secret cloudflared-token
kubectl -n cloudflared create secret generic cloudflared-token --from-literal=token=<new-token>
kubectl -n cloudflared rollout restart deploy/cloudflared
```

If the tunnel id changes, update both CNAME records to the new
`<tunnel-id>.cfargotunnel.com` target.

### On-LAN access is unchanged

`gsd.home.lab` still resolves through Pi-hole to the Traefik VIP and is served by
the existing ingress, independent of the tunnel. It is not behind Access.

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

## iOS Shortcut Setup (Voice Capture)

The capture pipeline uses iOS Shortcuts to send voice input directly to the n8n webhook:

1. Open the **Shortcuts** app on your iPhone
2. Create a new Shortcut named **"Capture"** (short name works best for Siri, Watch, and CarPlay)
3. **Action 1:** "Dictate Text" — captures your speech
4. **Action 2:** "Get Contents of URL"
   - URL: `http://<your-server-ip>:5678/webhook/capture`
   - Method: **POST**
   - Headers: `Content-Type: application/json`
   - Request Body (JSON): key `title`, value = the "Dictated Text" variable from Action 1

Now say **"Hey Siri, Capture"** from iPhone, Apple Watch, or CarPlay to send tasks straight to your inbox.

**Tip:** Keep the shortcut name to a single word ("Capture") for reliable Siri/Watch/CarPlay recognition. Multi-word names can be unreliable on watchOS.

You can also capture directly via the API:
```bash
curl -X POST http://localhost:8000/next-actions \
  -H "Content-Type: application/json" \
  -d '{"title": "Your task here"}'
```

Or use the **+ Capture** button at the top of the Intake page in the UI.

## n8n Workflows

Import the workflow JSON files from `n8n/workflows/` into your n8n instance:

1. **Inbox Capture** (`inbox-capture.json`) — Webhook receives `{ "title": "..." }` and creates an inbox item
2. **Weekly Digest** (`weekly-digest.json`) — Runs Sunday 7pm, queries the API for inbox items, stale actions, pending items, and projects missing next actions, then emails a formatted digest

To import: n8n UI → Workflows → Import from File.

## API Endpoints

```
GET    /tags                                 — all tags (ordered by sort_order)

GET    /projects                             — list projects (?root_only=true)
GET    /projects/:id                         — project detail (with links, children)
POST   /projects                             — create project
PATCH  /projects/:id                         — update project
DELETE /projects/:id                         — delete (re-parents children, unassigns tasks)

GET    /projects/:id/tasks                   — ordered active tasks
GET    /projects/:id/history                 — completed + deleted task history
PUT    /projects/:id/tasks/order             — reorder tasks

POST   /projects/:id/links                   — add link
PATCH  /projects/:id/links/:link_id          — update link
DELETE /projects/:id/links/:link_id          — remove link
PUT    /projects/:id/links/order             — reorder links

GET    /next-actions                         — list (filter: ?status=active&tag_ids=uuid1&tag_ids=uuid2)
POST   /next-actions                         — create
PATCH  /next-actions/:id                     — update
DELETE /next-actions/:id                     — soft delete (sets deleted_at)
```

Tag filtering uses AND logic: `?tag_ids=a&tag_ids=b` returns only actions tagged with **both** a and b.

Auto-generated API docs: `http://localhost:8000/docs`

## Tag Taxonomy

| Category | Tags (ordered) |
|----------|------|
| Context  | @home, @online, @errands, @calls |
| Time     | #now, #today, #week, #month, #someday |
| Energy   | +easy, +routine, +focused, +peak |

Tags within time and energy categories are ordered by intensity (ordinal data). Context tags are alphabetical.

## Data Model

- **next_actions** — the atomic unit. Status: inbox → active/pending → complete. Soft-deleted (preserves history).
- **tags** — first-class entities with sort_order. Joined via `next_action_tags`. AND-filter logic.
- **projects** — container for related actions. Supports 2-level hierarchy (parent → sub-projects). Status: active → complete.
- **project_links** — URL + label pairs attached to projects (JIRA-style references).
