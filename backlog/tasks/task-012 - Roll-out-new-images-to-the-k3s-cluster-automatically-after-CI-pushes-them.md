---
id: TASK-012
title: Roll out new images to the k3s cluster automatically after CI pushes them
status: To Do
assignee: []
created_date: '2026-10-05 03:56'
labels:
  - ci
  - infra
  - k8s
dependencies:
  - TASK-011
references:
  - k8s/api/deployment.yaml
  - k8s/ui/deployment.yaml
priority: medium
type: chore
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Once TASK-011 pushes tested images on every merge to main, the cluster still has to pick them up. Today that is a manual `kubectl -n gsd rollout restart deploy/api deploy/ui`. The goal (raised 2026-10-04) is that a merge to main means a deploy, with no manual step.

The open design question is how to trigger the rollout, since the k3s cluster (three Raspberry Pi nodes, ARM64) is on the home network and GitHub-hosted runners cannot reach its API. Candidates include a self-hosted GitHub runner on the LAN, an in-cluster image-update controller that watches Docker Hub, or GitOps (Argo CD / Flux) reconciling manifests from the repo. Choose one with the user before implementing. Migrations already run on rollout via the api deployment's `alembic upgrade head` init container, and a failed migration keeps the old pod serving.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The rollout mechanism is chosen with the user and the decision and its rationale are recorded in DECISIONS.md
- [ ] #2 After a merge to main, the api and ui deployments run the newly pushed images without any manual step
- [ ] #3 The deployments reference an immutable image (commit SHA tag or digest), so it is always possible to tell which commit is running
- [ ] #4 Opening a port on the home network or exposing the Kubernetes API to the internet is not required
- [ ] #5 A failed rollout (e.g. a failing migration in the init container) leaves the previous version serving and is visible to the user, not silent
- [ ] #6 The README documents how deploys happen and how to roll back to an earlier commit
<!-- AC:END -->
