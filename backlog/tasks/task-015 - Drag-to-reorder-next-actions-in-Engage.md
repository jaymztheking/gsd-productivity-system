---
id: TASK-015
title: Drag to reorder next actions in Engage
status: To Do
assignee: []
created_date: '2026-10-13 01:47'
labels:
  - ui
  - api
dependencies: []
references:
  - ui/src/pages/EngagePage.tsx
  - ui/src/components/ProjectTaskList.tsx
  - api/app/routers/projects.py
  - api/app/models/next_action.py
priority: medium
type: feature
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
James wants to put his next actions in his own priority order. The Engage list has no ordering control today, so items show in whatever order the API returns them, and he cannot pull the most important item to the top. He wants manual drag-to-reorder, not a sort-by-field dropdown. Tasks inside a project already have a persisted manual order (`project_sort_order` with a reorder endpoint on projects), which is a precedent to look at. The planned area columns in Engage will reuse this ordering within each column, so the order should be stored in a way that still holds once tasks are grouped by area.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Next actions in Engage can be reordered by drag-and-drop with a mouse on desktop and by touch on a phone
- [ ] #2 The order is saved on the server and survives a page reload and a different device
- [ ] #3 A newly created or newly activated task gets a defined, predictable position, such as the top or bottom, rather than a random one
- [ ] #4 Reordering while filters are applied does not scramble the relative order of tasks hidden by the filter
- [ ] #5 Tests cover the reorder API, including invalid or partial ID lists
<!-- AC:END -->
