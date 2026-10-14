---
id: TASK-017
title: Show Engage as columns grouped by area
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:48'
updated_date: '2026-10-14 01:52'
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
- [x] #1 Engage can display tasks as one vertical column per area, in area order, plus an "Unassigned" column for tasks without an area
- [x] #2 The existing Engage filters (context, time, energy, pending) still apply in the column view
- [x] #3 Tasks within each column follow the manual order from drag-to-reorder
- [x] #4 Dragging a card into a different column changes that task's area, and the change persists
- [x] #5 At phone width the column view stays usable, through horizontal column scrolling or a column picker, without horizontal page overflow
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Engage gets a List / Columns by area switch, remembered per browser in localStorage (try/catch)
2. EngageBoard: one dnd-kit DndContext with a SortableContext per column (areas in order, then Unassigned); column bodies are droppable so empty columns accept cards; columns are filtered views of the already-filtered, engage-ordered task list, so existing filters apply unchanged
3. Drag within a column: reorder with PUT /next-actions/order for that column's IDs (subset-within-slots keeps everything else in place). Drag across columns: card re-files live on drag-over; on drop PATCH area_id then PUT the destination column order; reload on failure
4. Layout: columns 300px wide, horizontal scroll with scroll-snap inside the board (page never overflows); 85% wide on phones so the next column peeks in; main-content widens to 1280px via :has() when the board shows
5. Verify with Playwright: columns in area order + Unassigned, filters, within-column reorder persists, cross-column drag changes area and persists, touch drag on a phone, no page overflow at 375px; docs
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented on branch task-017-engage-columns (commit cd594b7). UI only; no API changes were needed, since area columns reuse PATCH area_id (TASK-016) and the subset reorder (TASK-015).

Design: a List / Columns by area switch, remembered per browser in localStorage. EngageBoard has one dnd-kit context with a SortableContext per column, and droppable column bodies so empty columns accept drops. The card re-files into the hovered column during the drag; on drop it PATCHes area_id (if the column changed), then PUTs the destination column's order. Columns are 300px with horizontal scroll and scroll-snap inside the board, 85% wide at <=480px, and main-content widens to 1280px via :has() while the board shows. Unassigned is the last column.

Verification, 2026-10-13 (Playwright against local API + Postgres 15):
- Desktop 1280px: columns Home life, Health, Professional development, Unassigned, matching area order. Within-column mouse drag (Paint door above Water plants) reordered only that column. Dragging Fix tap into the empty Professional development column changed its area. Both survived a reload, and the API showed the new area_id and engage order. The view choice persisted across reload. The @home filter applied in columns (Unassigned emptied, Book dentist hidden). Page scrollWidth was 1280 (no overflow).
- Phone 375px with touch via CDP: page scrollWidth 375, board scrollWidth 1202 (columns scroll inside the board). Touch drag reordered within Home life. Holding a touch drag at the right edge auto-scrolled the board (scrollLeft 0 -> 303) and dropped Call bank into Professional development, which persisted.
- API unit suite 88 passed; npm run build passes.

Small leftover: cards in the column view still show their area badge, which repeats the column header. It's harmless and was left as is.

Not yet deployed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Engage has a List / Columns by area switch. The column view shows one column per area in area order plus Unassigned. The existing filters apply, cards follow the manual Engage order, and dragging a card into another column changes its area and saves the destination column's order. On phones the columns scroll sideways inside the board, with no page overflow. Verified with Playwright on desktop (mouse) and at 375px (touch, including edge auto-scroll across columns), with the results confirmed through the API and across reloads. Not yet deployed.
<!-- SECTION:FINAL_SUMMARY:END -->
