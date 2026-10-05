---
id: TASK-009
title: Add a Daily Routine tab with a per-weekday checklist that resets each day
status: To Do
assignee: []
created_date: '2026-10-05 03:28'
updated_date: '2026-10-05 03:31'
labels:
  - ui
  - api
  - feature
dependencies: []
references:
  - ui/src/components/Layout.tsx
  - ui/src/App.tsx
  - ui/src/pages/EngagePage.tsx
  - api/app/routers
  - api/app/models
priority: medium
type: feature
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The user has a set of things they expect to do on a regular daily cadence and wants to tick them off in GSD as the day goes on. The existing GSD objects do not fit: next actions and intake items are transient (completed once, then gone or archived), so re-entering the same items daily is friction and loses the "standing list" nature of a routine. Requested 2026-10-04: a new tab alongside Engage / Intake / Projects that shows a persistent checklist of routine items. Items can be checked off during the day and automatically come back unchecked the next day, while the list itself stays put until the user deliberately edits it.

A single every-day list is too rigid: the user wants a Monday routine, a Tuesday routine, and so on, so each item is scheduled on specific days of the week. The user also wants to see their track record over time (a heatmap, tracked separately as a follow-up task), so each day's completions must be kept as history rather than overwritten by the reset.

"End of day" should follow the user's local day, not UTC; the rest of the system (e.g. the weekly digest in n8n/workflows/weekly-digest.json) treats the user as being in America/Denver.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A "Routine" tab appears in the main navigation alongside Engage, Intake and Projects and opens a page showing today's routine checklist
- [ ] #2 Routine items are stored server-side via the API and database, so the list and today's check state are the same across devices and survive page reloads and container restarts
- [ ] #3 The user can add, rename, reorder and delete routine items from the Routine page
- [ ] #4 Each routine item is scheduled on one or more days of the week (any combination of Monday through Sunday), chosen when the item is created and changeable later
- [ ] #5 Today's checklist shows only the items scheduled for the current local weekday, and the user can view and edit items scheduled for other weekdays without switching the device date
- [ ] #6 Routine items are persistent: checking one off never deletes, archives or completes it as a task, and items do not show up in Engage, Intake, Projects or the weekly digest
- [ ] #7 The user can check and uncheck items any number of times during the day, and checked items are visually crossed off
- [ ] #8 At the start of each new local day (America/Denver), the checklist switches to that weekday's items, all unchecked, without any user action
- [ ] #9 The daily reset is correct even if no service was running at midnight or the page was left open across midnight (e.g. opening the app the next morning, or the next week, shows a fresh checklist)
- [ ] #10 Editing the list (add/rename/reorder/delete/reschedule) does not reset the check state of other items for the current day
- [ ] #11 Completion history is retained per item per local date after the reset, and an API endpoint returns, for a requested date range, each item's completed dates, its weekday schedule and the date it was created
- [ ] #12 Deleting a routine item removes it from the checklist but keeps its past completion history available to the history endpoint
- [ ] #13 API tests cover item CRUD, weekday scheduling, toggling check state, history retrieval, and the day-boundary reset including a Denver-vs-UTC boundary case
- [ ] #14 Routine endpoints are protected by the same API token auth as the rest of the API
<!-- AC:END -->
