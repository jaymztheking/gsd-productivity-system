---
id: TASK-021
title: Make tasks in a project always take the project's area of focus
status: Done
assignee:
  - '@James'
created_date: '2026-10-14 02:24'
updated_date: '2026-10-14 02:29'
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
- [x] #1 A task in a project reports the project's area, including no area when the project has none
- [x] #2 Changing a project's area changes the area of every task in that project, with no per-task edits
- [x] #3 The API refuses an attempt to set a different area on a task that belongs to a project, and setting a project and an area in the same request is resolved in favour of the project's area
- [x] #4 Moving a task into a project gives it the project's area. Removing it from its project leaves it with that area, which is then editable on the task
- [x] #5 Existing tasks in projects whose area differs from the project's are brought in line when the change ships
- [x] #6 In the UI, the area picker is replaced by the project's area (read-only) for tasks in a project, in Intake and in the Engage task editor
- [x] #7 In Engage columns view, dragging a project task into a different area column does not change its area, and the card returns to its column with a short explanation
- [x] #8 API tests cover inheritance, propagation on project area change, refusal of overrides, and leaving a project. DECISIONS.md, README and FILE-GLOSSARY describe the new rule
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

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on branch task-021-area-inheritance (commit 6def366).

Design: next_actions.area_id stays the stored value (Engage columns/filters read it). The API keeps it in sync instead of computing it on read. Create with project_id takes the project's area. PATCH project_id takes the project's area (an area_id in the same request is ignored). PATCH area_id alone on a project task gets 422 unless it equals the project's area (the editor may resend it). Project area change bulk-updates its tasks, including completed and deleted ones, so history stays consistent. Unknown project_id is now 422 instead of a FK error.
Bug fixed on the way: PATCH project_id null was ignored ('is not None'), so the UI's 'None' project never removed a task from its project. It now does, and the task keeps its area.
UI: AreaSelector takes the task's project and shows the project's area read-only with 'from project X'. The Engage editor sends area_id only for tasks without a project; leaving a project pre-selects the old project's area. EngageBoard refuses cross-column drags of project tasks (card stays) and shows a 5s notice naming the project.

Verification, 2026-10-13:
- API: test_areas.py rewritten for the rule (inheritance incl. none, create-time area ignored, propagation on project area change and clearing, 422 refusal for different area or null, same value accepted, project+area same request, move into project, leave project keeps then edits area, project delete keeps area, unknown project 422). Unit suite 95 passed; digest pipeline 12 passed against the local Postgres-backed API.
- Migration 010 on postgres:15-alpine with drifted data: the project task in the wrong area was aligned, the task in an area-less project went to none, and free tasks were untouched. Down/up clean.
- Postgres API: PATCH project area moved its task; PATCH different area on a project task returned 422.
- Playwright: Intake shows 3 area chips without a project and the read-only 'Professional development from project Get certified' with one. The Engage editor is the same. Setting project None pre-selects Professional development and the save persists with no project. Columns view (1280px): dragging 'Buy study guide' to Health showed the notice and left columns unchanged; dragging free task 'Call bank' to Home life persisted after reload.

Not yet deployed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Tasks in a project now always have the project's area. The API keeps them in sync: a project's area change moves all its tasks, a different area on a project task is refused, and a task that leaves its project keeps the area as its own. Migration 010 aligned existing tasks. The UI shows the area read-only for project tasks and refuses to drag them to another area column, with a note. Also fixed PATCH project_id null being ignored, so tasks can actually be removed from a project. Verified with rewritten area tests (95 API tests passing), a migration run on Postgres 15 with drifted data, and Playwright checks of Intake, the Engage editor and the columns board. Not yet deployed.
<!-- SECTION:FINAL_SUMMARY:END -->
