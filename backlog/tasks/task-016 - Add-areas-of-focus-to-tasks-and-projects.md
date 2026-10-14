---
id: TASK-016
title: Add areas of focus to tasks and projects
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 01:48'
updated_date: '2026-10-14 01:41'
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
- [ ] #1 Areas can be created, renamed, reordered and deleted, and the order is persisted
- [ ] #2 A next action has at most one area, and a project has at most one area
- [ ] #3 A new task added to a project that has an area defaults to that area, and the default can be overridden
- [ ] #4 The area can be set and changed in Intake, on a task in Engage, and on the project detail screen
- [ ] #5 Deleting an area leaves its tasks and projects unassigned rather than deleting them
- [ ] #6 The schema change ships as an Alembic migration, and API tests cover area CRUD and assignment
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
