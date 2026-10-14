---
id: TASK-021
title: Make tasks in a project always take the project's area of focus
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-14 02:24'
updated_date: '2026-10-14 02:25'
labels:
  - api
  - ui
dependencies:
  - TASK-016
references:
  - api/app/crud/next_actions.py
  - api/app/crud/projects.py
  - ui/src/components/AreaSelector.tsx
  - ui/src/pages/EngageBoard.tsx
  - DECISIONS.md
priority: medium
type: feature
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
TASK-016 made a task's area default to its project's area, but only once: when the task is created in or moved into the project. After that the task's area can be changed independently, and changing the project's area leaves its existing tasks behind. James wants area to belong to the project. A task in a project always has its project's area, including none when the project has no area, and cannot be given a different one. Tasks without a project keep their own editable area as they do today. This reverses the 'the default can be overridden' part of TASK-016 (its AC #3 and the DECISIONS.md 'Areas of Focus Are Their Own Entity' entry), which should be revised rather than left contradicting the behaviour. Sub-projects have their own area field like root projects, and their tasks follow the sub-project's area.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A task in a project reports the project's area, including no area when the project has none
- [ ] #2 Changing a project's area changes the area of every task in that project, with no per-task edits
- [ ] #3 The API refuses an attempt to set a different area on a task that belongs to a project, and setting a project and an area in the same request is resolved in favour of the project's area
- [ ] #4 Moving a task into a project gives it the project's area. Removing it from its project leaves it with that area, which is then editable on the task
- [ ] #5 Existing tasks in projects whose area differs from the project's are brought in line when the change ships
- [ ] #6 In the UI, the area picker is replaced by the project's area (read-only) for tasks in a project, in Intake and in the Engage task editor
- [ ] #7 In Engage columns view, dragging a project task into a different area column does not change its area, and the card returns to its column with a short explanation
- [ ] #8 API tests cover inheritance, propagation on project area change, refusal of overrides, and leaving a project. DECISIONS.md, README and FILE-GLOSSARY describe the new rule
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Keep next_actions.area_id as the stored value (Engage columns and filters read it) but make the API keep it in sync: create with project_id -> project's area (any area_id ignored); PATCH that sets project_id -> project's area (area_id in the same request ignored); PATCH area_id alone on a project task -> 422 unless equal to the project's area; PATCH project area -> UPDATE all its tasks
2. Fix PATCH project_id null being ignored (it used 'is not None'), so a task can actually leave its project; on leaving it keeps its area. Project delete already SET NULLs project_id and leaves area
3. Migration 010: align existing project tasks' area_id with their project's
4. UI: AreaSelector shows the project's area read-only for tasks in a project (Intake, Engage editor); editor sends area_id only for tasks without a project; EngageBoard refuses cross-column drags of project tasks and shows a short notice; project detail copy updated
5. Tests: rewrite TASK-016 override tests to the new rule, add propagation, refusal, same-request precedence, leave-project and project-delete tests; migration run on Postgres 15; Playwright check of read-only picker and refused drag
6. Docs: DECISIONS areas entry, README, FILE-GLOSSARY
<!-- SECTION:PLAN:END -->
