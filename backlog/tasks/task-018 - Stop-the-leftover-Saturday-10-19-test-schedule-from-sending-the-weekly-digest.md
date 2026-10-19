---
id: TASK-018
title: 'Stop the leftover Saturday 10:19 test schedule from sending the weekly digest'
status: Done
assignee:
  - '@James'
created_date: '2026-10-13 01:49'
updated_date: '2026-10-19 01:37'
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
- [x] #1 The source of the Saturday 10:19 sends is identified from n8n execution history and the live workflow and version state
- [x] #2 No schedule fires the digest outside Sunday 19:00 America/Denver
- [x] #3 The fix survives an n8n pod restart, because a restart re-registers schedules from the published state
- [x] #4 A full week passes with exactly one digest delivered, on Sunday at 19:00 local
- [x] #5 If the cause is a publish or import quirk, the README digest publishing steps are updated so future schedule tests clean up after themselves
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

Fix applied 2026-10-12 ~20:20 MT:
- kubectl -n n8n set image deploy/n8n n8n=n8nio/n8n:2.38.7@sha256:a8c95f75... (with change-cause annotation). The pod template change rolled n8n; the new pod n8n-786d5f49bf-5qqwc runs the same digest and reports 2.38.7.
- Startup log activated exactly two workflows from published state: GSD Inbox Capture (vumX7eNksFjrHSg1) and GSD Weekly Review Digest (wayvHwteu1n9IPRk). The orphaned 84f0c92c cron is gone with the old process.
- AC3: the fix is the restart itself, and the only thing re-registered is the published Sunday version, so later restarts produce the same result.
- Capture webhook OK after restart: POST to capture.medaughsolutions.com/webhook/capture without a token returns 403 (header-auth rejection; an unknown webhook path returns 404).
- README: added a note under Weekly Digest configuration to restart n8n after changing a published schedule through the CLI, and to treat the image pin as the upgrade control.
- Remaining: AC2 is confirmed when Sat Oct 17 10:19 MT passes with no execution, and AC4 when Sun Oct 18 19:00 MT produces exactly one. Re-run the read-only execution_entity query for wayvHwteu1n9IPRk after that.

Validation 2026-10-18 (Gmail inbox, accepted by James in place of the execution_entity query):
- Digests received: Sat Oct 10 10:19 MT (test cron, pre-fix), Sun Oct 11 19:00 MT, then none on Sat Oct 17 10:19 MT, and exactly one on Sun Oct 18 19:00 MT (Gmail 2026-10-19T01:00:19Z).
- AC2/AC4 rest on delivered email only; a Saturday run that fired but failed to send would not appear. The DB query was not run.
- n8n rolled twice more after the fix (deployment revisions 4 and 5; current pod started 2026-10-14T02:11Z, likely the TASK-020 password rotation). Image is still pinned to 2.38.7@sha256:a8c95f75, and the Oct 18 digest still sent correctly after those restarts, supporting AC3.
- Noticed: the digest subject uses the UTC date (Sunday 19:00 MT send is titled Monday, October 19). Not in scope here.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The Saturday 10:19 digests came from an orphaned in-memory cron left over from the Sep 26 schedule test (n8n Schedule Triggers are in-process crons; the CLI re-import changed only the DB). Fixed by pinning the live n8n deployment to n8nio/n8n:2.38.7@sha256:a8c95f75 and letting the rollout restart n8n, which re-registered only the published Sunday 19:00 America/Denver version. README now says to restart n8n after changing a published schedule through the CLI. Verified from the Gmail inbox: no digest on Sat Oct 17 10:19 MT and exactly one on Sun Oct 18 19:00 MT, including after later n8n restarts.
<!-- SECTION:FINAL_SUMMARY:END -->
