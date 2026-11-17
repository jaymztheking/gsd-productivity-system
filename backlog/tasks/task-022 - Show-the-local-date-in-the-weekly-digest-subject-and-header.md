---
id: TASK-022
title: Show the local date in the weekly digest subject and header
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-19 01:40'
updated_date: '2026-11-17 17:03'
labels:
  - n8n
  - digest
dependencies: []
references:
  - n8n/workflows/weekly-digest.json
  - README.md
priority: low
type: bug
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The weekly review digest is sent Sunday at 19:00 America/Denver, but its subject and header carry the next day's date. The Oct 18, 2026 digest arrived titled "GSD Weekly Review — Monday, October 19, 2026". The workflow timezone setting (America/Denver) only governs when the Schedule Trigger fires. The Code node formats the date with `toLocaleDateString` and no time zone, so it uses the n8n container clock, which is UTC, and Sunday 19:00 MT (01:00 UTC Monday) renders as Monday. A wrong date in the digest makes it look like it was sent late or on the wrong schedule, which already confused the TASK-018 investigation. Publishing note: after changing the live workflow through the CLI, restart n8n so the in-process cron is rebuilt from the published state (see the README Weekly Digest notes and TASK-018).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 The digest subject and header show the America/Denver calendar date of the send, so a Sunday 19:00 MT send reads Sunday
- [ ] #2 The date stays correct for a send in the evening after the UTC date has already rolled over, and across the DST change
- [ ] #3 The live n8n workflow is updated and published, and still fires only on Sunday at 19:00 America/Denver
- [ ] #4 The repo copy of the workflow matches the published live version
- [ ] #5 The next scheduled digest arrives with the correct local date in its subject
<!-- AC:END -->
