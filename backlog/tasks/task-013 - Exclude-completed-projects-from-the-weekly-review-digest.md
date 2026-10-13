---
id: TASK-013
title: Exclude completed projects from the weekly review digest
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 01:47'
updated_date: '2026-10-13 14:13'
labels:
  - digest
  - api
  - n8n
dependencies: []
references:
  - n8n/workflows/weekly-digest.json
  - api/app/routers/projects.py
  - api/app/crud/projects.py
  - api/tests/test_digest_pipeline.py
priority: medium
type: bug
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The weekly review digest lists completed projects under "Active Projects", which James reported after the 2026-10-11 digest. A weekly review is for deciding what to do next, so finished projects are noise in it, and each one is also flagged "NO NEXT ACTION", which is a false alarm. The workflow requests `/projects?status=active`, but the `GET /projects` route in `api/app/routers/projects.py` only accepts `root_only` and silently ignores `status`, so every root project comes back whatever its status. The UI may depend on the current unfiltered behaviour, so check it before changing the default.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The projects list endpoint honours a status filter, and `status=active` returns no completed projects
- [ ] #2 The weekly digest "Active Projects" section lists only active projects
- [ ] #3 The "NO NEXT ACTION" flag is never shown for a completed project
- [ ] #4 Existing UI views of projects behave the same as before, or any intended change is deliberate and noted
- [ ] #5 Tests cover the status filter, including the active-only case the digest relies on
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. GET /projects: add an optional status query param (ProjectStatus | None, default None = no filter), mirroring GET /next-actions; filter in crud list_projects
2. Leave the digest workflow unchanged: it already sends status=active, and its Compile Digest node renders and flags every project it receives, so filtering at the API fixes AC2 and AC3 without an n8n re-import or restart
3. UI unchanged: it only calls /projects?root_only=..., so the None default keeps its behaviour (AC4)
4. Tests in api/tests/test_projects.py, endpoint-level via TestClient on SQLite like test_routine.py: status=active, status=complete, no filter returns both, invalid status 422, combined with root_only
5. Rebuild and push the API image, roll out, verify live: /projects?status=active has no complete projects, unfiltered count unchanged
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Research 2026-10-13: ProjectStatus is active|complete. UI client.ts only calls /projects?root_only=${rootOnly}. Digest Fetch Active Projects calls http://api.gsd.svc.cluster.local:8000/projects?status=active; Compile Digest flags NO NEXT ACTION for any returned project without an active action. api/tests/test_digest_pipeline.py is a live integration test that sends no X-API-Token, so it has likely 401d since TASK-003; not used here.
<!-- SECTION:NOTES:END -->
