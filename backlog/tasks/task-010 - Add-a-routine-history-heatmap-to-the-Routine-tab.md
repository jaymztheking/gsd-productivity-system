---
id: TASK-010
title: Add a routine history heatmap to the Routine tab
status: To Do
assignee: []
created_date: '2026-10-05 03:31'
labels:
  - ui
  - feature
dependencies:
  - TASK-009
references:
  - ui/src/pages
priority: medium
type: feature
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Once the Routine tab (TASK-009) records daily completions, the user wants to see their consistency over time, in the spirit of the GitHub contribution graph. Unlike GitHub's weeks-by-weekday grid, the user asked for one row per routine item and one column per day across a range they choose, so they can see at a glance which habits are slipping. Requested 2026-10-04.

Because items run on specific weekdays (e.g. Monday-only), a day the item was not scheduled must not look like a miss. Uses the history endpoint delivered by TASK-009.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The Routine tab offers a history heatmap view with one row per routine item and one column per local date (America/Denver), oldest to newest left to right
- [ ] #2 The user can choose the date range shown, with quick presets (e.g. last 7 days, 30 days, 90 days) and a custom start/end date
- [ ] #3 Each cell clearly distinguishes three states: completed, scheduled but missed, and not scheduled that day; dates before an item was created count as not scheduled
- [ ] #4 Today's column reflects the live check state and is not shown as missed while the day is still in progress
- [ ] #5 Hovering or tapping a cell shows the item name, date and state
- [ ] #6 Each row shows the item's completion rate over the selected range, counting only scheduled days
- [ ] #7 Deleted items with history in the selected range still appear as rows, visibly marked as removed
- [ ] #8 Long ranges stay readable: the grid scrolls horizontally inside its container with item names pinned, and the page has no horizontal scroll at phone width
- [ ] #9 Colours meet contrast requirements in both light and dark themes and states are distinguishable without relying on colour alone
<!-- AC:END -->
