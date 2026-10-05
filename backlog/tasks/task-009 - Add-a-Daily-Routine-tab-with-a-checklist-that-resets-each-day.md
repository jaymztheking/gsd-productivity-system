---
id: TASK-009
title: Add a Daily Routine tab with a per-weekday checklist that resets each day
status: Done
assignee:
  - '@claude'
created_date: '2026-10-05 03:28'
updated_date: '2026-10-05 03:50'
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
- [x] #1 A "Routine" tab appears in the main navigation alongside Engage, Intake and Projects and opens a page showing today's routine checklist
- [x] #2 Routine items are stored server-side via the API and database, so the list and today's check state are the same across devices and survive page reloads and container restarts
- [x] #3 The user can add, rename, reorder and delete routine items from the Routine page
- [x] #4 Each routine item is scheduled on one or more days of the week (any combination of Monday through Sunday), chosen when the item is created and changeable later
- [x] #5 Today's checklist shows only the items scheduled for the current local weekday, and the user can view and edit items scheduled for other weekdays without switching the device date
- [x] #6 Routine items are persistent: checking one off never deletes, archives or completes it as a task, and items do not show up in Engage, Intake, Projects or the weekly digest
- [x] #7 The user can check and uncheck items any number of times during the day, and checked items are visually crossed off
- [x] #8 At the start of each new local day (America/Denver), the checklist switches to that weekday's items, all unchecked, without any user action
- [x] #9 The daily reset is correct even if no service was running at midnight or the page was left open across midnight (e.g. opening the app the next morning, or the next week, shows a fresh checklist)
- [x] #10 Editing the list (add/rename/reorder/delete/reschedule) does not reset the check state of other items for the current day
- [x] #11 Completion history is retained per item per local date after the reset, and an API endpoint returns, for a requested date range, each item's completed dates, its weekday schedule and the date it was created
- [x] #12 Deleting a routine item removes it from the checklist but keeps its past completion history available to the history endpoint
- [x] #13 API tests cover item CRUD, weekday scheduling, toggling check state, history retrieval, and the day-boundary reset including a Denver-vs-UTC boundary case
- [x] #14 Routine endpoints are protected by the same API token auth as the rest of the API
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Data model (migration 006): `routine_items` (title, weekdays as a 7-bit Mon..Sun mask, sort_order, created_on local date, deleted_at for soft delete) and `routine_completions` (item_id + completed_on local date, composite PK). A tick is a row for that local date; unticking deletes it.
2. Daily reset is implicit, not scheduled: "today" is computed per request from USER_TIMEZONE (new setting, default America/Denver) and today's state is just completions for that date. Nothing needs to run at midnight, and history is never overwritten. Add `tzdata` so zoneinfo works in the slim image and on Windows.
3. API router `/routine` behind the existing token auth: GET /routine/today (date, weekday, next_reset_at, scheduled items with completed flag); GET/POST /routine/items; PATCH/DELETE /routine/items/{id}; PUT /routine/items/order (reorders a subset, e.g. one weekday, keeping other items' slots); PUT /routine/items/{id}/completion {date, completed} rejecting a stale date with 409 so a page left open past midnight cannot tick into the wrong day; GET /routine/history?start&end returning per-item completed dates, weekdays, created_on and deleted_at, including deleted items.
4. API tests against in-memory SQLite (as test_next_action_tags.py does) with an injectable clock: CRUD, weekday filtering, toggling, reorder, history incl. deleted items, Denver-vs-UTC boundary, stale-date 409, plus auth coverage for the new router.
5. UI: Routine nav tab and /routine page with Today (checklist, crossed-off ticks, optimistic toggle) and Edit (weekday filter, add/rename/reschedule/delete, up/down reorder) views. Refetch at next_reset_at, on tab refocus, and on a 409. Tighten the nav so four tabs fit at phone width.
6. Update FILE-GLOSSARY / LOG docs; verify build, tests, and the page in a browser.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented per plan. Decisions: daily reset is implicit (completions keyed by local date in USER_TIMEZONE, default America/Denver), so nothing runs at midnight and history is never overwritten. Weekdays stored as a 7-bit mask (0=Mon..6=Sun), exposed as a list. Reorder accepts a subset (one weekday view) and keeps other items' slots. Completion PUT carries the client's date and returns 409 if it is not local today, so a page left open across midnight reloads instead of ticking the wrong day; ticking an unscheduled item is 422, unticking is always allowed. Deleted items are soft-deleted and still returned by /routine/history when they have completions in range. Items are a separate table, so they cannot leak into Engage/Intake/Projects or the digest (which reads /next-actions and /projects only). Added tzdata (slim image and Windows have no tz database).

Validation: api/tests/test_routine.py 39 tests pass (CRUD, validation, weekday filtering, tick/untick, stale-date 409, edits keep ticks, next-day/next-week reset, Denver-vs-UTC midnight boundary, DST next_reset_at, history incl. deleted items and range limits, 401 on all 8 routine endpoints); test_auth + test_next_action_tags still pass (55 total). test_digest_pipeline needs a live API and was not run. UI: vite build OK, app tsc clean. Browser check on local API (SQLite) + Vite: tab in nav, ticking crosses off and persists server-side, add/rename/reschedule/reorder/two-step delete work, ticks survive edits, no horizontal scroll at 375px and 320px. API restart: ticks persisted. Migration 006 rendered offline for Postgres (alembic --sql) but not applied to a live Postgres; Docker was not running.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a Routine tab: a standing checklist of items scheduled on chosen weekdays that can be ticked off during the day and comes back unticked at local (America/Denver) midnight. Backed by new routine_items/routine_completions tables (migration 006) and a token-protected /routine API; completions are kept per local date, with a history endpoint ready for the TASK-010 heatmap. Verified with 39 new API tests (including Denver-vs-UTC and DST boundaries), a production build, and a browser walkthrough of the Today and Edit views at desktop and phone widths.
<!-- SECTION:FINAL_SUMMARY:END -->
