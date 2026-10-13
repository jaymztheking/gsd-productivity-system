---
id: TASK-019
title: Track the live n8n deployment manifests and retire the stale k8s/n8n copy
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 02:21'
updated_date: '2026-10-13 02:23'
labels:
  - n8n
  - k8s
dependencies:
  - TASK-018
references:
  - k8s/n8n/deployment.yaml
  - README.md
priority: medium
type: chore
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The n8n instance that runs GSD capture and the weekly digest is deployment/n8n in namespace `n8n`, image pinned in TASK-018 to `n8nio/n8n:2.38.7@sha256:a8c95f75c6fdf65f5f2b7a7b354744eaa1c62bb911b5c00af6499c3f38e4cd32`. It was deployed from outside this repository, and no source for its manifests is known. The pin and its change-cause annotation exist only on the cluster, so re-applying n8n from wherever it originally came from would silently revert it to `:latest` and an unplanned upgrade.

Separately, `k8s/n8n/` in this repo (deployment, pvc, service) describes a different n8n in namespace `gsd` that was never deployed: it uses a Recreate strategy, basic-auth env from `gsd-config`, and no Postgres. Anyone reading the repo would reasonably take it for the live config, which already misled the TASK-018 investigation briefly.

Live facts as of 2026-10-12: Postgres-backed (`postgres-postgresql.postgres.svc.cluster.local`, database `n8n`, user `n8n`, password and `N8N_ENCRYPTION_KEY` from Secret `n8n-secrets`); `N8N_HOST=n8n.home.lab`, `WEBHOOK_URL=http://n8n.home.lab/`; data on PVC `n8n-data` (local-path, bound to node cherrypi); public capture route through the Cloudflare tunnel at capture.medaughsolutions.com. The live Deployment has env (such as `N8N_SECURE_COOKIE`) that is missing from its own last-applied annotation, so it has been hand-edited since it was applied.

The README calls this n8n "shared", so other workloads may depend on it. Find out before treating it as GSD-only. This is the same class of problem TASK-007 fixed for the MCP server: a component GSD depends on that is invisible to this repo.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The live n8n Deployment, Service, PVC, any ingress, and Secret references (names and keys only, never values) are captured as manifests from the cluster, including hand-edits that are not in last-applied
- [ ] #2 A decision is recorded on where those manifests live, in this repo or elsewhere, taking into account whether anything besides GSD uses this n8n
- [ ] #3 The tracked manifests keep the exact pinned image, so applying them never changes the n8n version
- [ ] #4 `kubectl diff` of the tracked manifests against the live cluster shows no changes
- [ ] #5 The stale `k8s/n8n/` copy is removed or replaced, so nothing in this repo describes an n8n that does not exist
- [ ] #6 README and FILE-GLOSSARY describe where the n8n manifests are and how to upgrade n8n by changing the pin
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Export the live n8n namespace objects (Namespace, Deployment, Service, Ingress, PVC) from the cluster and strip server-managed fields; capture Secret n8n-secrets as an example file with key names only
2. Replace the stale k8s/n8n/ (namespace gsd, never deployed) with these manifests, keeping the exact pinned image
3. kubectl diff -f k8s/n8n/ must show no changes; iterate until it does
4. Update README (k3s/n8n sections), FILE-GLOSSARY, and DECISIONS.md with where n8n lives and how to upgrade by changing the pin
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Research 2026-10-12:
- Live n8n objects (namespace n8n): Deployment n8n, Service n8n (80 -> 5678), Ingress n8n (n8n.home.lab, traefik), PVC n8n-data (1Gi local-path on cherrypi), Secret n8n-secrets (2 keys). All applied with kubectl client-side apply; Deployment later changed by kubectl set image/annotate (TASK-018) and has hand-edited env not in last-applied.
- Never in this repo: git history has no manifests for namespace n8n. The live n8n (280d) predates this repo's k8s/ (2026-03-01); k8s/n8n/ was a GSD-local design (namespace gsd) that was never deployed.
- Users: all 8 workflows on it are GSD (from the TASK-018 export); no other namespace or repo under ~/github references it; the only external reference is k8s/cloudflared capture route to n8n.n8n.svc.cluster.local:80. Its database lives in the separate postgres namespace (out of scope).
- Decision (AC2, user): track the live manifests in this repo at k8s/n8n, replacing the stale copy. GSD is its only user and the tunnel route that depends on it is already here.
<!-- SECTION:NOTES:END -->
