---
id: TASK-017
title: Show Engage as columns grouped by area
status: To Do
assignee: []
created_date: '2026-10-13 01:48'
labels:
  - ui
dependencies:
  - TASK-015
  - TASK-016
references:
  - ui/src/pages/EngagePage.tsx
  - ui/src/pages/FilterPanel.tsx
priority: low
type: feature
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Once tasks have areas (TASK-016) and a manual order (TASK-015), James wants to see his next actions laid out as vertical columns, one per area such as home life or professional development. This works like a board, so he can see at a glance how his work spreads across parts of his life and move items between them. Engage is used mostly from a phone, so the column layout cannot assume desktop width.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Engage can display tasks as one vertical column per area, in area order, plus an "Unassigned" column for tasks without an area
- [ ] #2 The existing Engage filters (context, time, energy, pending) still apply in the column view
- [ ] #3 Tasks within each column follow the manual order from drag-to-reorder
- [ ] #4 Dragging a card into a different column changes that task's area, and the change persists
- [ ] #5 At phone width the column view stays usable, through horizontal column scrolling or a column picker, without horizontal page overflow
<!-- AC:END -->
