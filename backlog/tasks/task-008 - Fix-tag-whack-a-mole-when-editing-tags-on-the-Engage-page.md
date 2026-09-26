---
id: TASK-008
title: Fix tag whack-a-mole when editing tags on the Engage page
status: Done
assignee:
  - '@claude'
created_date: '2026-09-26 14:17'
updated_date: '2026-09-26 15:55'
labels:
  - ui
  - bug
dependencies: []
references:
  - ui/src/pages/TaskCard.tsx
  - ui/src/pages/EngagePage.tsx
  - ui/src/components/TagSelector.tsx
  - api/app/crud/next_actions.py
priority: high
type: bug
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Editing a task's tags on the Engage page drops tags the user did not touch. Repro reported by the user (2026-09-26): task "Buy Anniversary card" was tagged only energy=easy. In the Engage card editor they added context=errands and time horizon=now and hit Save; the new tags were applied but energy=easy was removed. The result is "tag whack-a-mole": fixing one category knocks out another, so tags can never be set reliably and Engage filtering (which ANDs tags) becomes untrustworthy.

The API update replaces the whole tag set whenever `tag_ids` is sent (api/app/crud/next_actions.py), so whatever the UI sends on save must be the complete intended set. A lead worth checking first: TaskCard (ui/src/pages/TaskCard.tsx) seeds its per-category `selectedTags` state from `action.tags` only once on mount and never resyncs, so the editor state can diverge from the badges shown on the card. Confirm the actual root cause before fixing; do not assume this is it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Reproduce the reported case: a task tagged only energy=easy, then adding context and time tags in the Engage editor and saving, keeps energy=easy alongside the new tags
- [x] #2 Saving from the Engage editor never removes a tag in a category the user did not change
- [x] #3 Explicitly deselecting a tag in the editor and saving still removes that tag
- [x] #4 The tags pre-selected in the editor always match the tag badges displayed on the card, including after a previous save, a list refresh, or a filter change
- [x] #5 Behaviour is correct across repeated edit/save cycles on the same card without reloading the page
- [x] #6 Root cause is recorded in the implementation notes
- [x] #7 A regression test (UI or API, whichever layer holds the bug) covers the reported scenario
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Root cause (API): update_next_action runs a raw DELETE on next_action_tags, then assigns action.tags. The ORM collection still holds the pre-delete tags, so SQLAlchemy only INSERTs tags that are new; tags kept across the edit are deleted and never re-inserted. Fix: drop the raw DELETE and let the relationship assignment compute the diff (the collection is always eager-loaded via get_next_action/selectin).
2. Add an API regression test that runs update_next_action against a real DB session (SQLite in-memory via aiosqlite if the models allow it, else Postgres) covering: kept tag survives while others added (reported case), explicit removal, empty list clears, repeated edits.
3. UI hardening for AC4: TaskCard seeds editor state once on mount; re-seed title/notes/tags/project/status from the action prop whenever the editor is opened, so the editor always matches the badges.
4. Verify: run the new test (fails before fix, passes after), tsc build of the UI, and a manual check against the running app if available.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root cause (API, not UI): update_next_action ran a raw DELETE on next_action_tags, then assigned action.tags. The relationship collection was already loaded (selectinload in get_next_action) with the pre-edit tags and knew nothing of the raw DELETE, so the ORM diff only INSERTed tags that were new. Any tag kept across the edit (energy=easy in the report) was deleted and never re-inserted; re-saving an unchanged set wiped every tag. Removing a tag also made the ORM issue a second DELETE for rows already gone: SQLite raises StaleDataError on that, asyncpg does not check rowcounts so Postgres failed silently.
Fix: drop the raw DELETE and let the collection assignment compute the diff (api/app/crud/next_actions.py); removed the now-unused delete import.
UI hardening (AC4): TaskCard seeded editor state once on mount. It now re-seeds title/notes/tags/project/status from the action every time the editor opens, so it always starts from the badges shown and a cancelled edit no longer leaks into the next open.
Tests: new api/tests/test_next_action_tags.py runs the real crud functions against in-memory SQLite (aiosqlite, added to test deps), one session per step like per-request. Before fix: 5/6 failed, reported case stored {errands, now} without easy. After fix: 6/6 pass; with test_auth.py 19 passed.
Env notes (pre-existing, unrelated): test_auth.py needed asyncpg installed locally; ui tsc -b fails on vite.config.ts because @types/node is not installed in local node_modules. tsc -p tsconfig.app.json --noEmit is clean.

Committed 5fc412b on fix/task-008-engage-tag-whackamole. Checked AC2/3/5/7 on the API regression tests (19 passed) and AC6 on these notes. AC1 and AC4 stay open: they need a manual check in the deployed Engage page (no local Docker/DB available to run the UI end to end).

DEPLOYED 2026-09-26: gsd-api:latest@sha256:64a31eb3 and gsd-ui:latest@sha256:eda493a8 pushed to Docker Hub and rolled out to the gsd namespace; running pod imageIDs confirmed to match. The in-image UI build ran tsc -b cleanly, confirming the local vite.config.ts error is only missing @types/node on this machine.
LIVE API CHECK (prod Postgres, throwaway task): PATCH sequence [@errands #now +easy] from +easy only, same set re-saved, [@home #now +easy], [@home +easy], [] each stored exactly what was sent.
BROWSER CHECK (Chrome, gsd.medaughsolutions.com/engage, throwaway task 'ZZ TASK-008 tag test'): AC1 - card with only +easy, selected @errands and #now, Save -> card showed +easy @errands #now. After a full page reload the tags persisted and the editor pre-selected exactly those three (AC4 after save and refresh). Deselected #now, Save -> +easy @errands (AC3 in UI). Selected @home then Cancel, reopened -> editor showed @errands/+easy, discarded edit did not leak. Applied the +easy filter on Engage, reopened -> editor still matched the badges (AC4 after filter change). Throwaway task soft-deleted afterwards (DELETE 204, gone from list).
'Buy anniversary card' itself is complete with @errands #now +easy.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Editing tags on the Engage page dropped any tag the user kept (e.g. energy=easy vanished when adding context and time). The cause was in the API: update_next_action ran a raw DELETE on next_action_tags and then assigned action.tags, but the already-loaded collection still held the old tags, so the ORM only inserted new ones and kept tags were lost; re-saving an unchanged set wiped all tags. Fixed by removing the raw DELETE so the collection assignment computes the diff. TaskCard also now re-seeds its editor from the action every time it opens, so it always matches the card and cancelled edits don't carry over.

Verified with 6 new regression tests in api/tests/test_next_action_tags.py against in-memory SQLite (5 failed before the fix, all pass after; 19 with test_auth.py), a live PATCH sequence against production Postgres, and a Chrome walkthrough of the deployed Engage page covering the reported case, removal, reload, cancel and filter. Deployed as gsd-api@sha256:64a31eb3 and gsd-ui@sha256:eda493a8.
<!-- SECTION:FINAL_SUMMARY:END -->
