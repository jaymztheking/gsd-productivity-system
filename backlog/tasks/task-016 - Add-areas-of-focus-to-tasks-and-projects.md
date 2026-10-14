---
id: TASK-016
title: Add areas of focus to tasks and projects
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:48'
updated_date: '2026-10-14 02:13'
labels:
  - api
  - ui
dependencies: []
references:
  - api/app/models/next_action.py
  - api/app/models/project.py
  - ui/src/pages/IntakeCard.tsx
  - ui/src/pages/ProjectDetailPage.tsx
priority: medium
type: feature
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
James wants to group his work into broad areas of focus, such as home life and professional development. In GTD terms these are areas of responsibility, a level above projects. No such concept exists in the system yet. Projects group related tasks toward one outcome, and context tags (@home and so on) describe where a task can be done, not which part of life it serves, so neither fits. He chose a single area per task and per project, and tasks in a project should default to the project's area. Areas will drive a column layout in Engage, tracked separately, so their display order matters.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Areas can be created, renamed, reordered and deleted, and the order is persisted
- [x] #2 A next action has at most one area, and a project has at most one area
- [x] #3 A new task added to a project that has an area defaults to that area, and the default can be overridden
- [x] #4 The area can be set and changed in Intake, on a task in Engage, and on the project detail screen
- [x] #5 Deleting an area leaves its tasks and projects unassigned rather than deleting them
- [x] #6 The schema change ships as an Alembic migration, and API tests cover area CRUD and assignment
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Model + migration 008: areas table (id, name unique, sort_order, created_at, updated_at); nullable area_id FK on next_actions and projects with ON DELETE SET NULL
2. API: /areas CRUD (GET list ordered, POST, PATCH rename, DELETE) and PUT /areas/order; area_id on NextAction and Project create/update/out schemas
3. Defaulting: creating a next action in a project without an explicit area_id takes the project's area; setting project_id on update with no area_id given and the task has no area also takes it. Explicit area_id (including null) overrides. Distinguish 'not sent' from null via model_fields_set
4. Delete area leaves tasks/projects with area_id null (FK SET NULL; also explicit UPDATE for SQLite tests)
5. UI: Area type, client functions, useAreas hook; AreaSelector component (chip buttons like TagSelector); manage areas (create, rename, reorder up/down, delete) from an Areas section on the Projects page; area picker in IntakeCard task form, TaskCard editor, ProjectDetailPage; area badge on TaskCard
6. Tests: area CRUD, ordering, delete unassigns, task/project assignment, project default and override
7. Docs: README data model, FILE-GLOSSARY, DECISIONS entry on areas vs context tags; MCP server create_task gains area_id
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on branch task-016-areas (commit 9567e83).

Decisions: areas are a separate table, not a tag category (see DECISIONS.md). Management lives in a collapsible 'Areas of focus' section on the Projects page with up/down reorder (drag arrives with TASK-015/017). PATCH distinguishes an omitted area_id (leave alone) from null (clear) via model_fields_set. Defaulting: a new task with project_id and no area_id takes the project's area; an unassigned task moved into a project also takes it; an explicit area_id, including null, wins. In the UI editors the area follows the chosen project unless the user picked one by hand (areaAfterProjectChange). Unknown area IDs get 422, duplicate names 409. MCP server gains list_areas and area_id on create_task/create_project.

Verification, 2026-10-13:
- tests/test_areas.py, 13 tests (CRUD, order persistence, reorder validation, uniqueness, assignment, omitted vs null, project default and override, move into project, delete unassigns); full unit suite 78 passed; digest pipeline 12 passed against local Postgres API.
- Migration 008 up/down/up on postgres:15-alpine; deleting an area row directly in Postgres set next_actions.area_id to NULL (FK SET NULL works independently of the crud's explicit unassign).
- Playwright at 375px: add areas, duplicate name shows an error, tap-to-rename, move up, order survives reload; project detail area set and survives reload; Intake Make Task with project 'Get certified' pre-selects its area 'Professional development'; saved task shows the area badge in Engage; changing it in the Engage editor persists across reload; no horizontal overflow.
- npm run build passes.

Not yet deployed.

Deployed 2026-10-13 (~20:15 MT) from main 65355f3: images jaymztheking/gsd-api@sha256:bf35def8, gsd-ui@sha256:74dbadb3, gsd-mcp@sha256:9ac7511c (previous images kept as :pre-areas for rollback). API init container ran migrations 007-009 (alembic now 009). DB backup taken first: ~/gsd-backups/gsd-pre-areas-20261013-1956.dump. Checked live through gsd.home.lab: the API returns areas/someday/tags (#someday gone), Engage order populated, UI bundle has the new features.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added areas of focus: a new areas table (migration 008) with nullable area_id on next actions and projects, /areas CRUD and reorder endpoints, and project-area defaulting for tasks. The UI manages areas under 'Areas of focus' on the Projects page and lets you set the area in Intake, the Engage task editor and project detail, with area badges on task cards and project list items. Deleting an area unassigns rather than deletes. Verified with 13 new API tests (78 total passing), a migration up/down run and FK check on Postgres 15, and a Playwright walkthrough at phone width. Not yet deployed.
<!-- SECTION:FINAL_SUMMARY:END -->
