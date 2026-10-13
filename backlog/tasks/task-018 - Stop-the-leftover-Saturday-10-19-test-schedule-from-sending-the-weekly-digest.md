---
id: TASK-018
title: 'Stop the leftover Saturday 10:19 test schedule from sending the weekly digest'
status: In Progress
assignee:
  - '@James'
created_date: '2026-10-13 01:49'
updated_date: '2026-10-13 02:18'
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Identify the source of the Saturday 10:19 sends from execution history and live workflow/scheduler state (read-only)
2. Pin the live n8n deployment (namespace n8n, managed outside this repo) to the running version, n8nio/n8n:2.38.7@sha256:a8c95f75..., so the restart does not also upgrade n8n
3. The pin changes the pod template, so the rollout restarts n8n, which drops the orphaned in-memory cron and re-registers schedules from the published state only
4. Verify after restart: digest workflow still published at 4b7c61e0, capture webhook works, n8n logs show clean activation
5. Update README digest publishing steps: after testing a schedule by editing the trigger, restart n8n (or deactivate before re-importing) so the test cron is not orphaned
6. Wait for the week of Oct 12-18 and confirm exactly one digest, Sunday Oct 18 19:00 MT (AC4)
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Root cause (AC1), 2026-10-12:
- Execution history for wayvHwteu1n9IPRk (read-only query, run by the user): #81 Sat Oct 3 10:19 MT and #85 Sat Oct 10 10:19 MT ran workflowVersionId 84f0c92c (the Sep 26 test version); #82 Sun Oct 4 19:00 and #88 Sun Oct 11 19:00 ran 4b7c61e0 (the published version). Earlier executions have been pruned (14-day retention).
- Persisted state has no Saturday schedule: CLI export shows only wayvHwteu1n9IPRk published (activeVersionId 4b7c61e0, Sunday 19:00 America/Denver); the other 5 digest copies are archived/unpublished with no 10:19 trigger. n8n 2.38.7's scheduled_job and scheduled_task tables are empty, so Schedule Trigger nodes are not using the persistent scheduler; they are in-process crons.
- So the test version's cron is orphaned in memory: the UI publish of 84f0c92c on Sep 26 registered it in the main process; the CLI import that restored the Sunday version runs as a separate process and changed only the DB; the later UI publish of 4b7c61e0 added the Sunday cron without removing the old one. The n8n pod has not restarted since Sep 13, so both crons are still live.
- Fix: restart n8n so crons are rebuilt from published state. The user chose to pin the image first (deployment uses n8nio/n8n:latest; tag 2.38.7 has the same index digest as the running image, a8c95f75).
- Note: k8s/n8n/ in this repo is NOT the live n8n (it targets namespace gsd and was never deployed). The live n8n is in namespace n8n, managed outside this repo, so the pin is applied with kubectl directly.
<!-- SECTION:NOTES:END -->
