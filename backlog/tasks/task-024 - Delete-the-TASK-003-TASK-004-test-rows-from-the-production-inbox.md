---
id: TASK-024
title: Delete the TASK-003/TASK-004 test rows from the production inbox
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-17 15:52'
updated_date: '2026-11-17 17:00'
labels:
  - data
  - cleanup
dependencies:
  - TASK-004
priority: low
type: chore
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verifying the auth and tunnel work in TASK-003 and TASK-004 created two real next actions in the production database: "e2e-test" (id starting c91e49c6), created through the live n8n capture workflow, and "public capture test" (id starting 20da46c0), created through capture.medaughsolutions.com. TASK-004 noted they should be deleted during triage, but nothing records that they were. The ids are 8-character prefixes as logged, not full UUIDs. Left in place they clutter the inbox and the weekly digest, and anyone reading them later cannot tell they were tests. They may already have been deleted by hand, in which case this task only needs to confirm that.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Both rows are confirmed gone from the production database, either deleted by this task or found already absent
- [ ] #2 Only those two rows are removed: matching is by id prefix and title together, and no other next action is affected
- [ ] #3 The task notes record whether each row was deleted or already absent
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 research (read-only queries against postgres in namespace gsd):
- Deleting a next action is a soft delete: delete_next_action in api/app/crud/next_actions.py sets deleted_at, and the UI, Engage and digest queries filter on deleted_at IS NULL. 71 of 135 next_actions rows are soft-deleted.
- c91e49c6-1ffa-4a5a-a2b9-658f8bc26860 "e2e-test": soft-deleted 2026-09-26 06:07:41.
- 20da46c0-7fae-45cd-b3d1-90c3b2bc3ffa "public capture test": soft-deleted 2026-09-26 06:07:44.
- Both were deleted during TASK-004 itself, a few minutes before its final sweep, so the note there saying they were left behind was already out of date. Neither has rows in next_action_tags.
- The "Task 23 test" capture the user deleted today (f2fdf3ad) is soft-deleted the same way.
- Outside scope: "Test CarPlay capture" (a2c82dd0, from TASK-005) is not deleted; it has status complete.
<!-- SECTION:NOTES:END -->
