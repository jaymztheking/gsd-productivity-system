---
id: TASK-015
title: Drag to reorder next actions in Engage
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:47'
updated_date: '2026-10-14 02:13'
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
- [x] #1 Next actions in Engage can be reordered by drag-and-drop with a mouse on desktop and by touch on a phone
- [x] #2 The order is saved on the server and survives a page reload and a different device
- [x] #3 A newly created or newly activated task gets a defined, predictable position, such as the top or bottom, rather than a random one
- [x] #4 Reordering while filters are applied does not scramble the relative order of tasks hidden by the filter
- [x] #5 Tests cover the reorder API, including invalid or partial ID lists
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Migration 009: engage_sort_order int on next_actions, backfilled for open items by created_at
2. API: a task entering active or pending (on create or status change) is placed at the bottom (max+1). GET /next-actions orders active/pending by engage_sort_order then created_at; other statuses keep created_at (Intake stays oldest-first)
3. PUT /next-actions/order {ordered_ids}: reorders a subset of open (active+pending) items within the slots they already occupy, then renumbers densely, so tasks hidden by filters or in other area columns keep their relative order; 422 for duplicates, unknown, deleted or non-open IDs, or an empty list
4. UI: add dnd-kit (@dnd-kit/core, sortable, utilities, exact versions). Engage merges active+pending sorted by engage_sort_order; each TaskCard gets a grip handle (touch-action none) as the only drag activator so tapping a card still opens the editor; pointer + keyboard sensors; optimistic reorder, reload on failure
5. Tests: API reorder tests (full, partial/filtered subset, invalid lists, bottom placement on create and activation, ordering of GET)
6. Docs: revise DECISIONS 'Buttons over Drag-and-Drop' for Engage, README/FILE-GLOSSARY
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on branch task-015-engage-reorder (commit 5d0350d).

Decisions: dnd-kit chosen by James over hand-written pointer code; pinned @dnd-kit/core 6.3.1, sortable 10.0.0, utilities 3.2.2 (bundle +~16 KB gzipped). New tasks go to the bottom (James's choice). One engage_sort_order shared by active and pending; Engage with Show Pending now interleaves them by that order instead of active-then-pending. Switching active<->pending keeps the place; entering from inbox/someday/complete goes to the bottom. Reorder is a subset-within-slots operation like the routine reorder, which is what keeps hidden tasks in place (AC4) and is what TASK-017 will reuse per column. Only the grip starts a drag (touch-action none), so card taps still open the editor. Inbox ordering stays created_at so Intake is unchanged. DECISIONS 'Buttons over Drag-and-Drop' revised.

Verification, 2026-10-13:
- tests/test_engage_order.py, 10 tests: bottom placement on create, activation from inbox/someday and reopen; full and partial reorders; active/pending share one order; inbox stays oldest-first; 422 for empty, duplicate, unknown, inbox, deleted and malformed IDs with no change; completed tasks leave the order. Unit suite 88 passed; digest pipeline 12 passed.
- Migration 009 up/down/up on postgres:15-alpine; backfill numbered open items 0..n oldest first. Tag-filtered GET on Postgres (JOIN/GROUP BY path) returns engage order.
- Playwright: desktop mouse drag moved 'Water plants' from bottom to top, persisted across reload; tapping a card still opens the editor. Phone 375px with touch events via CDP: with @home filter on, touch-dragging one card above another reordered only those, and the unfiltered list after reload kept the hidden tasks in their slots; holding a drag at the top edge auto-scrolled (scrollY 102 -> 0) and dropped at the top. No horizontal overflow.
- npm run build passes.

Not yet deployed.

Deployed 2026-10-13 (~20:15 MT) from main 65355f3: images jaymztheking/gsd-api@sha256:bf35def8, gsd-ui@sha256:74dbadb3, gsd-mcp@sha256:9ac7511c (previous images kept as :pre-areas for rollback). API init container ran migrations 007-009 (alembic now 009). DB backup taken first: ~/gsd-backups/gsd-pre-areas-20261013-1956.dump. Checked live through gsd.home.lab: the API returns areas/someday/tags (#someday gone), Engage order populated, UI bundle has the new features.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Engage tasks can now be reordered by dragging a grip on each card, with mouse, touch or keyboard (dnd-kit). The order is stored server-side in next_actions.engage_sort_order (migration 009), shared by active and pending tasks; new and newly activated tasks go to the bottom. PUT /next-actions/order reorders just the shown tasks within their existing slots, so filters (and the upcoming area columns) never scramble hidden tasks. Verified with 10 new API tests (88 total passing), a migration run on Postgres 15, and Playwright mouse and touch drags including filtered reorders, reload persistence and edge auto-scroll. Not yet deployed.
<!-- SECTION:FINAL_SUMMARY:END -->
