---
id: TASK-018
title: 'Stop the leftover Saturday 10:19 test schedule from sending the weekly digest'
status: To Do
assignee: []
created_date: '2026-10-13 01:49'
labels:
  - n8n
  - digest
dependencies:
  - TASK-006
references:
  - n8n/workflows/weekly-digest.json
  - README.md
priority: medium
type: bug
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The weekly review digest is now sent twice a week. James received one on Saturday 2026-10-10 at 10:19 and another on Sunday 2026-10-11 at 19:00. Only the Sunday 19:00 America/Denver send is wanted. The Saturday time is not random. While verifying TASK-006 on 2026-09-26, the trigger on live workflow wayvHwteu1n9IPRk was temporarily set to Saturday 10:19 America/Denver and published from the UI. The Sunday version was then re-imported and published, and a CLI export showed only the Sunday trigger as the active version (activeVersionId 4b7c61e0). The test schedule still fires weekly anyway. Possible causes include a schedule registration that was never torn down when the version changed, another published copy or version that still carries the 10:19 trigger, or a CLI import/publish that did not replace what the running process registered. See the TASK-006 implementation notes for the import and publish quirks in n8n 2.38.7 (CLI publish only applies after a restart, and import resets the workflow to unpublished).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The source of the Saturday 10:19 sends is identified from n8n execution history and the live workflow and version state
- [ ] #2 No schedule fires the digest outside Sunday 19:00 America/Denver
- [ ] #3 The fix survives an n8n pod restart, because a restart re-registers schedules from the published state
- [ ] #4 A full week passes with exactly one digest delivered, on Sunday at 19:00 local
- [ ] #5 If the cause is a publish or import quirk, the README digest publishing steps are updated so future schedule tests clean up after themselves
<!-- AC:END -->
