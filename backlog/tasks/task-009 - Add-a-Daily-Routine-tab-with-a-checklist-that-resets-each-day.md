---
id: TASK-009
title: Add a Daily Routine tab with a checklist that resets each day
status: To Do
assignee: []
created_date: '2026-10-05 03:28'
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
The user has a set of things they expect to do every day and wants to tick them off in GSD as the day goes on. The existing GSD objects do not fit: next actions and intake items are transient (completed once, then gone or archived), so re-entering the same items daily is friction and loses the "standing list" nature of a routine. Requested 2026-10-04: a new tab alongside Engage / Intake / Projects that shows a persistent checklist of daily routine items. Items can be checked off during the day and automatically come back unchecked the next day, while the list itself stays put until the user deliberately edits it.

"End of day" should follow the user's local day, not UTC; the rest of the system (e.g. the weekly digest in n8n/workflows/weekly-digest.json) treats the user as being in America/Denver.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A "Routine" (or "Daily Routine") tab appears in the main navigation alongside Engage, Intake and Projects and opens a page listing the routine items
- [ ] #2 Routine items are stored server-side via the API and database, so the list and today's check state are the same across devices and survive page reloads and container restarts
- [ ] #3 The user can add, rename, reorder and delete routine items from the Routine page
- [ ] #4 Routine items are persistent: checking one off never deletes, archives or completes it as a task, and items do not show up in Engage, Intake, Projects or the weekly digest
- [ ] #5 The user can check and uncheck items any number of times during the day, and checked items are visually crossed off
- [ ] #6 At the start of each new local day (America/Denver), every item shows as unchecked without any user action
- [ ] #7 The daily reset is correct even if no service was running at midnight or the page was left open across midnight (e.g. opening the app the next morning, or the next week, shows all items unchecked)
- [ ] #8 Editing the list (add/rename/reorder/delete) does not reset the check state of other items for the current day
- [ ] #9 API tests cover CRUD for routine items, toggling check state, and the day-boundary reset including a Denver-vs-UTC boundary case
- [ ] #10 Routine endpoints are protected by the same API token auth as the rest of the API
<!-- AC:END -->
