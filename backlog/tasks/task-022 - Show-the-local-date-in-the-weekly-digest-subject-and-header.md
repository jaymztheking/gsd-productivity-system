---
id: TASK-022
title: Show the local date in the weekly digest subject and header
status: In Progress
assignee:
  - '@claude'
created_date: '2026-10-19 01:40'
updated_date: '2026-11-17 17:08'
labels:
  - n8n
  - digest
dependencies: []
references:
  - n8n/workflows/weekly-digest.json
  - README.md
modified_files:
  - n8n/workflows/weekly-digest.json
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
- [x] #1 The digest subject and header show the America/Denver calendar date of the send, so a Sunday 19:00 MT send reads Sunday
- [x] #2 The date stays correct for a send in the evening after the UTC date has already rolled over, and across the DST change
- [x] #3 The live n8n workflow is updated and published, and still fires only on Sunday at 19:00 America/Denver
- [x] #4 The repo copy of the workflow matches the published live version
- [ ] #5 The next scheduled digest arrives with the correct local date in its subject
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Compile Digest: pass timeZone: 'America/Denver' to toLocaleDateString so dateStr (used in subject and header) is the local calendar date. The n8n container clock is UTC and n8n 2.38.7 bundles full ICU (78.3), so Intl can do the conversion.
2. Check the expression in the n8n pod for a Sunday 19:00 send on both sides of the DST change.
3. Import the patched JSON over wayvHwteu1n9IPRk keeping its id and live credential ids (same route as TASK-014), publish with the CLI, restart n8n so the in-memory cron is rebuilt (TASK-018).
4. Export the published version and confirm: Sunday 19:00 America/Denver trigger only, new date code present, nodes otherwise match the repo copy. Capture webhook still answers 403 without a token.
5. AC5 is confirmed by the next scheduled digest (Sun 2026-11-22 19:00 MT).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-11-17 research: live wayvHwteu1n9IPRk (published versionId e799fb61) matches n8n/workflows/weekly-digest.json node for node, ignoring ids, positions and credentials. Live credentials: GSD API Token oYF4SIR6WgX2VZQd on the five fetch nodes, SMTP account ygBtEFn5e291oEMk on Send Digest Email. In the n8n pod: ICU 78.3, process time zone UTC, and the Oct 18 send instant 2026-10-19T01:00:19Z formats as "Sunday, October 18, 2026" with timeZone America/Denver.

2026-11-17 implementation:
- Compile Digest now formats dateStr with timeZone: 'America/Denver'. dateStr feeds both the subject and the header.
- Ran the patched Compile Digest code in the n8n pod (UTC clock) with Date fixed to four send instants; all render Sunday in subject and header: 2026-10-19T01:00:19Z -> Sunday, October 18, 2026 (MDT); 2026-11-02T02:00Z -> Sunday, November 1, 2026 (day DST ends); 2026-11-23T02:00Z -> Sunday, November 22, 2026 (MST); 2027-03-15T01:00Z -> Sunday, March 14, 2027 (day DST starts).
- Deployed: took the live export, swapped in the new jsCode only, imported over wayvHwteu1n9IPRk (same id and credential ids), publish:workflow, then rollout restart deploy/n8n.
- After restart: list:workflow --active=true shows only GSD Inbox Capture and GSD Weekly Review Digest. Published version 0adc5397 has the Sunday 19:00 weeks trigger, workflow timezone America/Denver, the new date code, all credentials attached, and matches the repo copy node for node (ignoring ids, positions, credentials). Capture webhook without a token returns 403.
- AC #5 waits on the Sun 2026-11-22 19:00 MT digest.
<!-- SECTION:NOTES:END -->
