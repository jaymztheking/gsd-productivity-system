---
id: TASK-007
title: Restore the GSD MCP server after API token auth
status: Done
assignee:
  - '@James'
created_date: '2026-09-26 05:02'
updated_date: '2026-10-13 02:06'
labels:
  - mcp
  - auth
  - security
dependencies:
  - TASK-003
references:
  - k8s/secrets.yaml.example
  - README.md
priority: high
type: bug
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The GSD MCP server calls the GSD API with no authentication and breaks once TASK-003 auth is deployed. This was discovered while deploying TASK-003 and the deployment proceeded anyway at the user request, so the breakage is known and deliberate rather than accidental.

What is known about it, gathered from the cluster since it is not described anywhere in this repository:

- `deployment/mcp` in the `gsd` namespace, running for roughly 141 days
- image `jaymztheking/gsd-mcp:latest`
- env: `GSD_API_URL=http://api`, `MCP_TRANSPORT=sse`, `PORT=8080`
- `service/mcp` ClusterIP on port 8080
- no env sourced from any Secret or ConfigMap, so it has no token and no way to obtain one
- its manifests are NOT in this repository, so it was deployed from elsewhere, and no local source checkout could be found under ~/github

Because it reaches the API at `http://api` with no credential, every call it makes now returns 401. Its logs showed only `/health` polling, which remains unauthenticated, so it is not known whether it was actively serving real API traffic or sitting idle; that should be established early since it determines urgency.

The fix is to have it send the `X-API-Token` header with the value from the `API_TOKEN` key of the `gsd-secrets` Secret, the same secret the api and ui deployments already read. Its source repository must be located first.

Worth deciding as part of this work: whether the MCP manifests and source should be tracked in this repository or remain separate. Having a component that calls the GSD API but is invisible to the GSD repo is what allowed this break to go unnoticed until deployment.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The MCP server source repository is located and recorded, along with how its image is built and pushed
- [x] #2 Whether the MCP server was actively serving API traffic before the break is established, so the impact is understood rather than assumed
- [x] #3 The MCP server sends the `X-API-Token` header on every GSD API call, with the value read from configuration rather than hardcoded
- [x] #4 Its deployment sources `API_TOKEN` from the existing `gsd-secrets` Secret, consistent with the api and ui deployments
- [x] #5 A rebuilt ARM64 image is pushed and rolled out, and the MCP server successfully reads and writes GSD data through the authenticated API
- [x] #6 A decision is recorded on whether the MCP manifests and source belong in this repository, so a future API change cannot silently break it again
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Recover server.py and requirements.txt from the running gsd-mcp image (no source repo exists anywhere) into mcp/ in this repo, and write a Dockerfile for it
2. Read API_TOKEN from env and send it as X-API-Token on every request via the shared httpx client; fail fast at startup if it is unset
3. Add k8s/mcp/ manifests (deployment, service, ingress) mirroring what is live, with GSD_API_URL=http://api:8000 and API_TOKEN from gsd-secrets, like api/ui
4. Build the ARM64 (plus amd64, matching the existing multi-arch tag) image, push, apply, and roll out
5. Verify end-to-end over SSE: list_tags/list_projects read, and create_task writes, through the authenticated API
6. Update README and DECISIONS.md: where the MCP server lives, how it is built, and why it is tracked here
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Research findings (2026-10-12):
- No source repo exists: not on GitHub (jaymztheking has only gsd-productivity-system) and not on disk. The only copy is /app/server.py + requirements.txt inside the running image (Python, mcp==1.27.0, starlette SSE transport, 5 tools: capture_to_inbox, list_tags, list_projects, create_task, create_project). Image is multi-arch (amd64 + arm64) on Docker Hub.
- Live deployment was hand-patched after apply: last-applied has GSD_API_URL=http://gsd.home.lab, live has http://api. Also exposed via ingress gsd-mcp-ingress at mcp.gsd.home.lab (traefik, web entrypoint). Not referenced in any local Claude config.
- Impact (AC #2): pod has 69,732 log lines since its restart 28 days ago, all GET /health. No /sse or /messages requests at all, so it served no real traffic for at least 3 weeks before TASK-003 deployed (~7 days ago). The break had no user impact.
- Decision (user): bring source and manifests into this repo.

Implementation (2026-10-12), commits on task-007-mcp-token-auth:
- Found two more pre-existing bugs, both of which had to be fixed for AC #5. They mean the server could never have worked as deployed, independent of auth:
  1. GSD_API_URL=http://api has no port, and service/api is on 8000: connections failed outright.
  2. /sse was a Starlette Mount, so the SSE transport advertised /sse/messages/, which routed back into the SSE handler. The MCP handshake hung forever for every client. Changed to a Route per the MCP SDK pattern.
  Also: paths used an /api prefix that only exists on the ui nginx proxy (from the original gsd.home.lab URL). Dropped, since we now call api:8000 directly.
- Verified locally: ARM64 image without API_TOKEN exits at startup (KeyError). With the token, against the live API via port-forward, a real MCP SSE client got list_tags (13), list_projects (6), and create_task worked (test task bc2de063 created then deleted, 204).
- Blocked: pushing jaymztheking/gsd-mcp:latest to Docker Hub was denied by the auto-mode permission check (public registry). Needs user approval, then kubectl apply -f k8s/mcp/ and an in-cluster verification.

Rollout (2026-10-12): user pushed jaymztheking/gsd-mcp:latest (multi-arch, manifest sha256:6b1d16a1...). kubectl apply -f k8s/mcp/ (deployment configured, service/ingress unchanged) and rollout restart; new pod runs digest 6b1d16a1. In-cluster verification from the pod itself (GSD_API_URL=http://api:8000, API_TOKEN from gsd-secrets): MCP SSE client got list_tags 13, list_projects 6, create_task succeeded (test task 9a7234ce created then deleted, 204). Zero 401s in api logs since rollout.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Restored the GSD MCP server and brought it into this repo. No source repo existed, so server.py was recovered from the running image (mcp/, committed verbatim first). The server now sends X-API-Token from API_TOKEN, which the deployment reads from gsd-secrets like api/ui; a missing token fails at startup. Also fixed three pre-existing bugs that meant it could never have worked as deployed: wrong API port (http://api to http://api:8000), an /api path prefix that only exists on the ui proxy, and a Mount-vs-Route SSE bug that hung every client handshake. Added Dockerfile, k8s/mcp manifests, and README/FILE-GLOSSARY/DECISIONS entries. Impact of the original break was nil: 28 days of logs showed only health checks. Verified by a real MCP SSE client inside the cluster doing reads (tags, projects) and a write (create_task, then cleaned up), with zero 401s on the api.
<!-- SECTION:FINAL_SUMMARY:END -->
