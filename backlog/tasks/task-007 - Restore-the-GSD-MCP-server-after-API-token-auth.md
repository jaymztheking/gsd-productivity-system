---
id: TASK-007
title: Restore the GSD MCP server after API token auth
status: To Do
assignee: []
created_date: '2026-09-26 05:02'
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
- [ ] #1 The MCP server source repository is located and recorded, along with how its image is built and pushed
- [ ] #2 Whether the MCP server was actively serving API traffic before the break is established, so the impact is understood rather than assumed
- [ ] #3 The MCP server sends the `X-API-Token` header on every GSD API call, with the value read from configuration rather than hardcoded
- [ ] #4 Its deployment sources `API_TOKEN` from the existing `gsd-secrets` Secret, consistent with the api and ui deployments
- [ ] #5 A rebuilt ARM64 image is pushed and rolled out, and the MCP server successfully reads and writes GSD data through the authenticated API
- [ ] #6 A decision is recorded on whether the MCP manifests and source belong in this repository, so a future API change cannot silently break it again
<!-- AC:END -->
