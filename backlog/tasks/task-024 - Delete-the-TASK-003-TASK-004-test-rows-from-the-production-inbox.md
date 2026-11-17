---
id: TASK-024
title: Delete the TASK-003/TASK-004 test rows from the production inbox
status: To Do
assignee: []
created_date: '2026-11-17 15:52'
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
