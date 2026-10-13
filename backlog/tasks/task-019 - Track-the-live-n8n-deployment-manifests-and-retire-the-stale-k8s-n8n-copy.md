---
id: TASK-019
title: Track the live n8n deployment manifests and retire the stale k8s/n8n copy
status: To Do
assignee:
  - '@James'
created_date: '2026-10-13 02:21'
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
