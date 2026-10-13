---
id: TASK-013
title: Exclude completed projects from the weekly review digest
status: To Do
assignee: []
created_date: '2026-10-13 01:47'
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
