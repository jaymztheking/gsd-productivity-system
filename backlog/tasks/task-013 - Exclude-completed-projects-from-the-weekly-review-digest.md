---
id: TASK-013
title: Exclude completed projects from the weekly review digest
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:47'
updated_date: '2026-10-13 14:17'
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
- [x] #1 The projects list endpoint honours a status filter, and `status=active` returns no completed projects
- [x] #2 The weekly digest "Active Projects" section lists only active projects
- [x] #3 The "NO NEXT ACTION" flag is never shown for a completed project
- [x] #4 Existing UI views of projects behave the same as before, or any intended change is deliberate and noted
- [x] #5 Tests cover the status filter, including the active-only case the digest relies on
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

Verification 2026-10-13:
- Tests: new api/tests/test_projects.py (6 endpoint tests on SQLite). Full suite (auth, next_action_tags, routine, projects) 61 passed on python:3.12-slim. With the fix stashed, 5 of the 6 fail; the unfiltered test passes both ways, which is the UI-unchanged guarantee.
- Live before (old image adea0277): /projects?status=active returned 6 (4 active, 2 complete).
- Rollout: user pushed jaymztheking/gsd-api:latest (arm64, sha256:669f9294...); rollout restart api; new pod on that digest.
- Live after: ?status=active 4 (all active); ?status=complete 2; unfiltered and ?root_only=false unchanged at 6; ?status=bogus 422. UI path gsd.home.lab/api/projects?root_only=true 200. No 5xx in api logs.
- Digest (AC2/AC3): ran the digest's exact requests from inside the n8n pod: the Active Projects input is 4 active projects, 2 legitimately flagged NO NEXT ACTION, no completed projects. Did not run the workflow itself, to avoid sending an email and adding an execution during the TASK-018 observation week. First real digest with the fix: Sun 2026-10-18 19:00 MT.
- No workflow change and no n8n restart.
- Side note: the pushed image resolved newer unpinned deps (e.g. fastapi 0.143, sqlalchemy 2.1.4, starlette 1.8); the tests ran against the same resolution.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
GET /projects silently ignored ?status=, so the weekly digest's request for active projects returned completed ones too, each flagged NO NEXT ACTION. Added an optional status filter (ProjectStatus, default no filter) to the route and crud, mirroring GET /next-actions; invalid values now 422 instead of being ignored. The UI never sends status, so its lists are unchanged; the digest workflow already sends status=active, so it needed no change. Covered by api/tests/test_projects.py (5 of 6 fail without the fix); verified live after rollout: status=active returns 4 active projects instead of 6, unfiltered still 6, and the digest's own request from the n8n pod returns no completed projects.
<!-- SECTION:FINAL_SUMMARY:END -->
