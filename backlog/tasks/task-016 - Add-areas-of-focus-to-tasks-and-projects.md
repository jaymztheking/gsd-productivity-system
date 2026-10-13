---
id: TASK-016
title: Add areas of focus to tasks and projects
status: To Do
assignee: []
created_date: '2026-10-13 01:48'
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
